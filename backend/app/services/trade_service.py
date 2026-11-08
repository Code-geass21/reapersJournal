from sqlalchemy.orm import Session
from fastapi import HTTPException
from datetime import datetime, timezone
from decimal import Decimal

from app.models.trade import Trade, TradeConditionCheck, TradeExecution
from app.models.instrument import Instrument
from app.models.strategy import Strategy, StrategyRule
from app.schemas.trade import TradeCreate, TradeUpdate, TradeExecutionCreate
from app.services import pnl_service, log_service, alert_service

def _evaluate_rule_violations(db: Session, strategy_id: int, trade_in: TradeCreate) -> dict:
    rules = db.query(StrategyRule).filter(StrategyRule.strategy_id == strategy_id).all()
    violations = {}
    check_map = {c.rule_id: c.passed for c in trade_in.condition_checks}

    for rule in rules:
        if rule.is_required and not check_map.get(rule.id, False):
            violations[f"rule_{rule.id}"] = f"Required rule '{rule.label}' was not passed."

        params = rule.params or {}
        if rule.rule_type == 'risk':
            if params.get('requires_sl', False) and not trade_in.stop_loss:
                violations['risk_no_sl'] = f"Risk Rule '{rule.label}' requires a Stop Loss."

            max_lot = params.get('max_lot_size')
            if max_lot and trade_in.size > max_lot:
                violations['risk_max_lot'] = f"Size {trade_in.size} exceeds maximum {max_lot} lots."

            min_rr = params.get('min_rr')
            if min_rr:
                if not trade_in.stop_loss or not trade_in.take_profit:
                    violations['risk_min_rr_missing'] = f"Rule '{rule.label}' requires both SL and TP to evaluate Minimum RR."
                else:
                    entry = float(trade_in.entry_price)
                    sl = float(trade_in.stop_loss)
                    tp = float(trade_in.take_profit)

                    risk = (entry - sl) if trade_in.direction == 'long' else (sl - entry)
                    reward = (tp - entry) if trade_in.direction == 'long' else (entry - tp)

                    if risk > 0:
                        calc_rr = reward / risk
                        if calc_rr < float(min_rr):
                            violations['risk_min_rr'] = f"Trade RR ({calc_rr:.2f}) is below strategy minimum ({min_rr})."
                    else:
                        violations['risk_invalid_sl'] = "Invalid Stop Loss placement. Risk must be > 0."
    return violations

def _calculate_weighted_r_multiple(db: Session, trade: Trade) -> float:
    # FIX FOR BUG 52: Use the initial stop loss to calculate R, preventing breaks when SL is moved to breakeven
    if not trade.initial_stop_loss:
        return None

    exits = db.query(TradeExecution).filter(
        TradeExecution.trade_id == trade.id,
        TradeExecution.execution_type == 'exit'
    ).all()

    if not exits:
        return None

    # Use exact Decimal math to prevent precision drift
    total_exited_size = sum(Decimal(str(e.size)) for e in exits)
    if total_exited_size == Decimal('0'):
        return None

    weighted_sum = sum(Decimal(str(e.price)) * Decimal(str(e.size)) for e in exits)
    weighted_exit_price = float(weighted_sum / total_exited_size)

    return pnl_service.calculate_r_multiple(
        direction=trade.direction,
        entry_price=float(trade.entry_price),
        exit_price=weighted_exit_price,
        stop_loss=float(trade.initial_stop_loss)
    )

def _recalculate_trade_metrics(db: Session, trade: Trade, instrument: Instrument):
    """
    FIX FOR BUG 54: Single source of truth for P&L math.
    Rebuilds booked P&L and R-multiple entirely from executions.
    """
    exits = db.query(TradeExecution).filter(
        TradeExecution.trade_id == trade.id,
        TradeExecution.execution_type == 'exit'
    ).all()

    inst_dict = {"contract_size": instrument.contract_size, "pip_size": instrument.pip_size, "quote_ccy": instrument.quote_ccy}

    total_pnl = Decimal('0')
    try:
        for ex in exits:
            pnl_data = pnl_service.calculate_pnl(
                db=db,
                direction=trade.direction,
                entry_price=float(trade.entry_price),
                exit_price=float(ex.price),
                size=float(ex.size),
                instrument=inst_dict
            )
            total_pnl += Decimal(str(pnl_data['pnl_realized']))
    except ValueError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

    if trade.status == 'closed':
        # FIX FOR BUG 53: Deduct fees exactly once when fully closed, allowing for post-trade fee edits.
        fees = Decimal(str(trade.fees or '0'))
        trade.pnl_realized = float(total_pnl - fees)
        if trade.initial_stop_loss:
            trade.r_multiple = _calculate_weighted_r_multiple(db, trade)
    else:
        trade.pnl_realized = float(total_pnl)


def create_trade(db: Session, user_id: int, trade_in: TradeCreate) -> Trade:
    strategy = db.query(Strategy).filter(Strategy.id == trade_in.strategy_id, Strategy.user_id == user_id).first()
    if not strategy:
        raise HTTPException(status_code=403, detail="Invalid strategy or you do not own it.")

    instrument = db.query(Instrument).filter(Instrument.id == trade_in.instrument_id).first()
    if not instrument:
        raise HTTPException(status_code=400, detail="Invalid instrument.")

    trade_data = trade_in.model_dump(exclude={"condition_checks", "initial_execution"})

    # FIX FOR BUG 52: Record initial risk on creation
    if trade_in.stop_loss and not trade_in.initial_stop_loss:
        trade_data['initial_stop_loss'] = trade_in.stop_loss

    new_trade = Trade(**trade_data, user_id=user_id)

    violations = _evaluate_rule_violations(db, trade_in.strategy_id, trade_in)
    new_trade.rule_violations = violations

    db.add(new_trade)
    db.flush()

    if trade_in.initial_execution:
        exec_data = trade_in.initial_execution.model_dump()
        new_execution = TradeExecution(**exec_data, trade_id=new_trade.id)
    else:
        new_execution = TradeExecution(
            trade_id=new_trade.id,
            execution_type='entry',
            price=trade_in.entry_price,
            size=trade_in.size,
            executed_at=datetime.now(timezone.utc)
        )
    db.add(new_execution)

    for check_data in trade_in.condition_checks:
        new_check = TradeConditionCheck(**check_data.model_dump(), trade_id=new_trade.id)
        db.add(new_check)

    if violations:
        violation_text = " | ".join(violations.values())
        alert_message = f"Discipline breach on new trade: {violation_text}"
        alert_service.create_alert(db, user_id, 'rule_violation', alert_message, new_trade.id)

    log_service.write(db, action="trade.create", user_id=user_id, entity_type="trade", entity_id=new_trade.id)

    db.commit()
    db.refresh(new_trade)
    return new_trade


def update_trade(db: Session, user_id: int, trade_id: int, trade_in: TradeUpdate) -> Trade:
    # Always lock the row during structural updates
    trade = db.query(Trade).with_for_update().filter(Trade.id == trade_id, Trade.user_id == user_id).first()
    if not trade:
        db.rollback()
        raise HTTPException(status_code=404, detail="Trade not found")

    update_data = trade_in.model_dump(exclude_unset=True)

    if 'strategy_id' in update_data and update_data['strategy_id'] != trade.strategy_id:
        strategy = db.query(Strategy).filter(Strategy.id == update_data['strategy_id'], Strategy.user_id == user_id).first()
        if not strategy:
            db.rollback()
            raise HTTPException(status_code=403, detail="Invalid strategy or you do not own it.")

    if 'instrument_id' in update_data and update_data['instrument_id'] != trade.instrument_id:
        instrument = db.query(Instrument).filter(Instrument.id == update_data['instrument_id']).first()
        if not instrument:
            db.rollback()
            raise HTTPException(status_code=400, detail="Invalid instrument.")

    exits = db.query(TradeExecution).filter(
        TradeExecution.trade_id == trade.id,
        TradeExecution.execution_type == 'exit'
    ).all()
    total_exited = sum(Decimal(str(e.size)) for e in exits)
    current_open_size = Decimal(str(trade.size)) - total_exited

    # FIX FOR BUG 51: Prevent open size from going negative via form edits
    if 'size' in update_data:
        new_size = Decimal(str(update_data['size']))
        if new_size < total_exited:
            db.rollback()
            raise HTTPException(status_code=400, detail=f"Cannot reduce total size below already exited amount ({total_exited} lots).")

    if trade.status == 'closed':
        forbidden_edits = ['entry_price', 'size', 'direction', 'instrument_id', 'strategy_id', 'status', 'exit_price']
        if any(k in update_data for k in forbidden_edits):
            db.rollback()
            raise HTTPException(status_code=400, detail="Cannot modify core financial details of a closed trade.")

    if trade.status == 'open' and ('entry_price' in update_data or 'size' in update_data):
        entry_exec = db.query(TradeExecution).filter(
            TradeExecution.trade_id == trade.id,
            TradeExecution.execution_type == 'entry'
        ).order_by(TradeExecution.executed_at.asc()).first()

        if entry_exec:
            if 'entry_price' in update_data:
                entry_exec.price = update_data['entry_price']
            if 'size' in update_data:
                entry_exec.size = update_data['size']

    # Handle Trade Closure via full form update
    if trade.status == 'open' and update_data.get('status') == 'closed':
        if not update_data.get('exit_price'):
            db.rollback()
            raise HTTPException(status_code=400, detail="Exit price is required to close a trade")

        closed_at = update_data.get('closed_at') or datetime.now(timezone.utc)
        update_data['closed_at'] = closed_at

        exit_execution = TradeExecution(
            trade_id=trade.id,
            execution_type='exit',
            price=update_data['exit_price'],
            size=float(current_open_size),
            executed_at=closed_at
        )
        db.add(exit_execution)
        db.flush()

    re_eval_needed = any(k in update_data for k in ['entry_price', 'size', 'direction', 'stop_loss', 'take_profit'])

    for key, value in update_data.items():
        setattr(trade, key, value)

    # Re-evaluate strategy constraints based on edits
    if re_eval_needed and trade.status == 'open':
        checks_data = [{"rule_id": c.rule_id, "passed": c.passed} for c in trade.condition_checks]
        current_state = TradeCreate(
            strategy_id=trade.strategy_id,
            instrument_id=trade.instrument_id,
            direction=trade.direction,
            entry_price=float(trade.entry_price),
            size=float(trade.size),
            stop_loss=float(trade.stop_loss) if trade.stop_loss else None,
            take_profit=float(trade.take_profit) if trade.take_profit else None,
            condition_checks=checks_data
        )

        new_violations = _evaluate_rule_violations(db, trade.strategy_id, current_state)

        if trade.rule_violations != new_violations:
            trade.rule_violations = new_violations
            if new_violations:
                violation_text = " | ".join(new_violations.values())
                alert_service.create_alert(db, user_id, 'rule_violation', f"Trade edit triggered rule breach: {violation_text}", trade.id)

    # Route all edits / closures through the master metrics function
    instrument = db.query(Instrument).filter(Instrument.id == trade.instrument_id).first()
    _recalculate_trade_metrics(db, trade, instrument)

    log_service.write(db, action="trade.update", user_id=user_id, entity_type="trade", entity_id=trade.id)

    db.commit()
    db.refresh(trade)
    return trade


def add_execution(db: Session, user_id: int, trade_id: int, exec_in: TradeExecutionCreate) -> Trade:
    trade = db.query(Trade).with_for_update().filter(Trade.id == trade_id, Trade.user_id == user_id).first()
    if not trade:
        db.rollback()
        raise HTTPException(status_code=404, detail="Trade not found")

    if trade.status in ['closed', 'cancelled']:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Cannot add executions to a {trade.status} trade")

    if exec_in.execution_type != 'exit':
        db.rollback()
        raise HTTPException(status_code=400, detail="Only exit executions can be logged manually.")

    if exec_in.price <= 0:
        db.rollback()
        raise HTTPException(status_code=400, detail="Execution price must be strictly greater than 0.")

    # FIX FOR BUG 50: Use strict Decimal math to prevent precision ghost lots (e.g. 0.001 left open)
    exits = db.query(TradeExecution).filter(
        TradeExecution.trade_id == trade.id,
        TradeExecution.execution_type == 'exit'
    ).all()

    total_exited = sum(Decimal(str(e.size)) for e in exits)
    current_open_size = Decimal(str(trade.size)) - total_exited

    exec_size = Decimal(str(exec_in.size))
    if exec_size <= Decimal('0') or exec_size > current_open_size:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Invalid size. Must be between 0.01 and {current_open_size}")

    execution_time = exec_in.executed_at if exec_in.executed_at else datetime.now(timezone.utc)

    # FIX FOR BUG 55: Validate execution bounds properly against DB records
    now_utc = datetime.now(timezone.utc)
    trade_opened = trade.opened_at.replace(tzinfo=timezone.utc) if trade.opened_at.tzinfo is None else trade.opened_at

    if execution_time < trade_opened:
        db.rollback()
        raise HTTPException(status_code=400, detail="Execution time cannot be before the trade was opened.")
    if execution_time > now_utc:
        db.rollback()
        raise HTTPException(status_code=400, detail="Execution time cannot be in the future.")

    new_exec = TradeExecution(
        trade_id=trade.id,
        execution_type='exit',
        price=exec_in.price,
        size=exec_in.size,
        executed_at=execution_time,
        note=exec_in.note
    )
    db.add(new_exec)
    db.flush()

    new_open_size = current_open_size - exec_size
    instrument = db.query(Instrument).filter(Instrument.id == trade.instrument_id).first()

    # Liquidate when completely flat
    if new_open_size <= Decimal('0.00001'):
        trade.status = 'closed'
        trade.closed_at = execution_time
        trade.exit_price = exec_in.price

    # Single source of truth calculation guarantees correct P&L matching
    _recalculate_trade_metrics(db, trade, instrument)

    log_service.write(db, action="trade.add_execution", user_id=user_id, entity_type="trade", entity_id=trade.id)

    db.commit()
    db.refresh(trade)
    return trade
