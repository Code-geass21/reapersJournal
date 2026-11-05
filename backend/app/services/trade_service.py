from sqlalchemy.orm import Session
from fastapi import HTTPException
from datetime import datetime, timezone

from app.models.trade import Trade, TradeConditionCheck, TradeExecution
from app.models.instrument import Instrument
from app.models.strategy import Strategy, StrategyRule
from app.schemas.trade import TradeCreate, TradeUpdate
from app.services import pnl_service, log_service, alert_service
from app.schemas.trade import TradeExecutionCreate

def _evaluate_rule_violations(db: Session, strategy_id: int, trade_in: TradeCreate) -> dict:
    rules = db.query(StrategyRule).filter(StrategyRule.strategy_id == strategy_id).all()
    violations = {}

    check_map = {c.rule_id: c.passed for c in trade_in.condition_checks}

    for rule in rules:
        if rule.is_required and not check_map.get(rule.id, False):
            violations[f"rule_{rule.id}"] = f"Required rule '{rule.label}' was not passed."

        params = rule.params or {}
        if rule.rule_type == 'risk':
            # 1. Enforce Mandatory Stop Loss
            if params.get('requires_sl', False) and not trade_in.stop_loss:
                violations['risk_no_sl'] = f"Risk Rule '{rule.label}' requires a Stop Loss."

            # 2. Enforce Max Lot Size
            max_lot = params.get('max_lot_size')
            if max_lot and trade_in.size > max_lot:
                violations['risk_max_lot'] = f"Size {trade_in.size} exceeds maximum {max_lot} lots."

            # 3. Enforce Minimum Risk-to-Reward (RR)
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
    if not trade.stop_loss:
        return None

    # Get all exit executions
    exits = db.query(TradeExecution).filter(
        TradeExecution.trade_id == trade.id,
        TradeExecution.execution_type == 'exit'
    ).all()

    if not exits:
        return None

    total_exited_size = sum(float(e.size) for e in exits)
    if total_exited_size == 0:
        return None

    # Calculate weighted average exit price
    weighted_sum = sum(float(e.price) * float(e.size) for e in exits)
    weighted_exit_price = weighted_sum / total_exited_size

    return pnl_service.calculate_r_multiple(
        direction=trade.direction,
        entry_price=float(trade.entry_price),
        exit_price=weighted_exit_price,
        stop_loss=float(trade.stop_loss)
    )

def create_trade(db: Session, user_id: int, trade_in: TradeCreate) -> Trade:
    strategy = db.query(Strategy).filter(Strategy.id == trade_in.strategy_id, Strategy.user_id == user_id).first()
    if not strategy:
        raise HTTPException(status_code=403, detail="Invalid strategy or you do not own it.")

    instrument = db.query(Instrument).filter(Instrument.id == trade_in.instrument_id).first()
    if not instrument:
        raise HTTPException(status_code=400, detail="Invalid instrument.")

    trade_data = trade_in.model_dump(exclude={"condition_checks", "initial_execution"})
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
    trade = db.query(Trade).filter(Trade.id == trade_id, Trade.user_id == user_id).first()
    if not trade:
        raise HTTPException(status_code=404, detail="Trade not found")

    update_data = trade_in.model_dump(exclude_unset=True)

    if 'strategy_id' in update_data and update_data['strategy_id'] != trade.strategy_id:
        strategy = db.query(Strategy).filter(Strategy.id == update_data['strategy_id'], Strategy.user_id == user_id).first()
        if not strategy:
            raise HTTPException(status_code=403, detail="Invalid strategy or you do not own it.")

    if 'instrument_id' in update_data and update_data['instrument_id'] != trade.instrument_id:
        instrument = db.query(Instrument).filter(Instrument.id == update_data['instrument_id']).first()
        if not instrument:
            raise HTTPException(status_code=400, detail="Invalid instrument.")

    if trade.status == 'closed':
        forbidden_edits = ['entry_price', 'size', 'direction', 'instrument_id', 'strategy_id', 'status', 'exit_price']
        if any(k in update_data for k in forbidden_edits):
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

    # Handle Trade Closure & Math
    if trade.status == 'open' and update_data.get('status') == 'closed':
        if not update_data.get('exit_price'):
            raise HTTPException(status_code=400, detail="Exit price is required to close a trade")

        if not update_data.get('closed_at'):
            update_data['closed_at'] = datetime.now(timezone.utc)

        instrument = db.query(Instrument).filter(Instrument.id == trade.instrument_id).first()
        inst_dict = {"contract_size": instrument.contract_size, "pip_size": instrument.pip_size, "quote_ccy": instrument.quote_ccy}

        # Calculate current open size by subtracting exited lots
        exits = db.query(TradeExecution).filter(
            TradeExecution.trade_id == trade.id,
            TradeExecution.execution_type == 'exit'
        ).all()
        total_exited = sum(float(e.size) for e in exits)
        current_open_size = float(trade.size) - total_exited

        # Calculate P&L for the final chunk being closed
        pnl_data = pnl_service.calculate_pnl(
            db=db,
            direction=update_data.get('direction', trade.direction),
            entry_price=float(update_data.get('entry_price', trade.entry_price)),
            exit_price=update_data['exit_price'],
            size=current_open_size,
            instrument=inst_dict
        )

        current_fees = float(update_data.get('fees', trade.fees or 0))

        # Accumulate the previously booked P&L and deduct fees
        already_booked_pnl = float(trade.pnl_realized or 0)
        final_chunk_pnl = pnl_data['pnl_realized']
        update_data['pnl_realized'] = already_booked_pnl + final_chunk_pnl - current_fees

        exit_execution = TradeExecution(
            trade_id=trade.id,
            execution_type='exit',
            price=update_data['exit_price'],
            size=current_open_size,
            executed_at=update_data['closed_at']
        )
        db.add(exit_execution)
        db.flush() # Ensure the new execution is available for weighted R-multiple

        if trade.stop_loss:
            update_data['r_multiple'] = _calculate_weighted_r_multiple(db, trade)

    for key, value in update_data.items():
        setattr(trade, key, value)

    log_service.write(db, action="trade.update", user_id=user_id, entity_type="trade", entity_id=trade.id)

    db.commit()
    db.refresh(trade)
    return trade

def add_execution(db: Session, user_id: int, trade_id: int, exec_in: TradeExecutionCreate) -> Trade:
    trade = db.query(Trade).filter(Trade.id == trade_id, Trade.user_id == user_id).first()
    if not trade:
        raise HTTPException(status_code=404, detail="Trade not found")

    if trade.status == 'closed':
        raise HTTPException(status_code=400, detail="Cannot add executions to a closed trade")

    if exec_in.execution_type != 'exit':
        raise HTTPException(status_code=400, detail="Only exit executions can be logged manually.")

    # Calculate the true open size dynamically
    exits = db.query(TradeExecution).filter(
        TradeExecution.trade_id == trade.id,
        TradeExecution.execution_type == 'exit'
    ).all()

    total_exited = sum(float(e.size) for e in exits)
    current_open_size = float(trade.size) - total_exited

    if exec_in.size <= 0 or exec_in.size > current_open_size:
        raise HTTPException(status_code=400, detail=f"Invalid size. Must be between 0.01 and {current_open_size}")

    instrument = db.query(Instrument).filter(Instrument.id == trade.instrument_id).first()
    inst_dict = {"contract_size": instrument.contract_size, "pip_size": instrument.pip_size, "quote_ccy": instrument.quote_ccy}

    # Calculate P&L specifically for this exited chunk
    pnl_data = pnl_service.calculate_pnl(
        db=db,
        direction=trade.direction,
        entry_price=float(trade.entry_price),
        exit_price=exec_in.price,
        size=exec_in.size,
        instrument=inst_dict
    )

    # Accumulate the realized P&L
    current_pnl = float(trade.pnl_realized or 0.0)
    trade.pnl_realized = current_pnl + pnl_data['pnl_realized']

    # We DO NOT modify trade.size here anymore so the original entry size is preserved

    new_exec = TradeExecution(
        trade_id=trade.id,
        execution_type='exit',
        price=exec_in.price,
        size=exec_in.size,
        executed_at=datetime.now(timezone.utc),
        note=exec_in.note
    )
    db.add(new_exec)
    db.flush() # Ensure the new execution is available for weighted R-multiple

    new_open_size = current_open_size - exec_in.size

    # Auto-close the trade if the entire position is liquidated
    if new_open_size <= 0.00001:  # Float math safety tolerance
        trade.status = 'closed'
        trade.closed_at = datetime.now(timezone.utc)
        trade.exit_price = exec_in.price

        # Deduct total fees on the final close
        trade.pnl_realized = float(trade.pnl_realized) - float(trade.fees or 0)

        if trade.stop_loss:
            trade.r_multiple = _calculate_weighted_r_multiple(db, trade)

    log_service.write(db, action="trade.add_execution", user_id=user_id, entity_type="trade", entity_id=trade.id)

    db.commit()
    db.refresh(trade)
    return trade
