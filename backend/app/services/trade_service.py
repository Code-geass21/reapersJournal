from sqlalchemy.orm import Session
from fastapi import HTTPException
from datetime import datetime, timezone

from app.models.trade import Trade, TradeConditionCheck, TradeExecution
from app.models.instrument import Instrument
from app.models.strategy import StrategyRule
from app.schemas.trade import TradeCreate, TradeUpdate
from app.services import pnl_service, log_service, alert_service

def _evaluate_rule_violations(db: Session, strategy_id: int, trade_in: TradeCreate) -> dict:
    """Evaluates trade parameters and manual checks against strategy rules."""
    rules = db.query(StrategyRule).filter(StrategyRule.strategy_id == strategy_id).all()
    violations = {}

    # Map frontend manual checks
    check_map = {c.rule_id: c.passed for c in trade_in.condition_checks}

    for rule in rules:
        # 1. Enforce required manual checklist items
        if rule.is_required and not check_map.get(rule.id, False):
            violations[f"rule_{rule.id}"] = f"Required rule '{rule.label}' was not passed."

        # 2. Auto-evaluate Risk Rules based on JSONB params
        params = rule.params or {}
        if rule.rule_type == 'risk':
            # Example: Enforce Stop Loss
            if params.get('requires_sl', False) and not trade_in.stop_loss:
                violations['risk_no_sl'] = f"Risk Rule '{rule.label}' requires a Stop Loss."

            # Example: Enforce Max Position Size
            max_lot = params.get('max_lot_size')
            if max_lot and trade_in.size > max_lot:
                violations['risk_max_lot'] = f"Size {trade_in.size} exceeds maximum {max_lot} lots."

    return violations

def create_trade(db: Session, user_id: int, trade_in: TradeCreate) -> Trade:
    trade_data = trade_in.model_dump(exclude={"condition_checks", "initial_execution"})
    new_trade = Trade(**trade_data, user_id=user_id)

    # Run the rule engine
    violations = _evaluate_rule_violations(db, trade_in.strategy_id, trade_in)
    new_trade.rule_violations = violations

    db.add(new_trade)
    db.flush() # Flush to get the new_trade.id

    # CREATE the initial TradeExecution
    if trade_in.initial_execution:
        exec_data = trade_in.initial_execution.model_dump()
        new_execution = TradeExecution(**exec_data, trade_id=new_trade.id)
    else:
        # Fallback if no explicit execution payload is sent
        new_execution = TradeExecution(
            trade_id=new_trade.id,
            execution_type='entry',
            price=trade_in.entry_price,
            size=trade_in.size,
            executed_at=datetime.now(timezone.utc)
        )
    db.add(new_execution)

    # Save the manual condition checks
    for check_data in trade_in.condition_checks:
        new_check = TradeConditionCheck(**check_data.model_dump(), trade_id=new_trade.id)
        db.add(new_check)

    # Fire a disciplinary alert if rules were broken
    if violations:
        violation_text = " | ".join(violations.values())
        alert_message = f"Discipline breach on new trade: {violation_text}"
        alert_service.create_alert(db, user_id, 'rule_violation', alert_message, new_trade.id)

    # Write to master audit log
    log_service.write(db, action="trade.create", user_id=user_id, entity_type="trade", entity_id=new_trade.id)

    db.commit()
    db.refresh(new_trade)
    return new_trade

def update_trade(db: Session, user_id: int, trade_id: int, trade_in: TradeUpdate) -> Trade:
    trade = db.query(Trade).filter(Trade.id == trade_id, Trade.user_id == user_id).first()
    if not trade:
        raise HTTPException(status_code=404, detail="Trade not found")

    update_data = trade_in.model_dump(exclude_unset=True)

    # Handle Trade Closure & Math
    if trade.status == 'open' and update_data.get('status') == 'closed':
        if not update_data.get('exit_price'):
            raise HTTPException(status_code=400, detail="Exit price is required to close a trade")

        instrument = db.query(Instrument).filter(Instrument.id == trade.instrument_id).first()
        inst_dict = {"contract_size": instrument.contract_size, "pip_size": instrument.pip_size, "quote_ccy": instrument.quote_ccy}

        pnl_data = pnl_service.calculate_pnl(
            db=db,
            direction=trade.direction,
            entry_price=float(trade.entry_price),
            exit_price=update_data['exit_price'],
            size=float(trade.size),
            instrument=inst_dict
        )
        update_data['pnl_realized'] = pnl_data['pnl_realized']

        if trade.stop_loss:
            update_data['r_multiple'] = pnl_service.calculate_r_multiple(
                direction=trade.direction,
                entry_price=float(trade.entry_price),
                exit_price=update_data['exit_price'],
                stop_loss=float(trade.stop_loss)
            )

        if not update_data.get('closed_at'):
            update_data['closed_at'] = datetime.utcnow()

    for key, value in update_data.items():
        setattr(trade, key, value)

    log_service.write(db, action="trade.update", user_id=user_id, entity_type="trade", entity_id=trade.id)

    db.commit()
    db.refresh(trade)
    return trade
