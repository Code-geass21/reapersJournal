from sqlalchemy.orm import Session
from fastapi import HTTPException
from datetime import datetime

from app.models.trade import Trade, TradeConditionCheck
from app.models.instrument import Instrument
from app.schemas.trade import TradeCreate, TradeUpdate
from app.services import pnl_service, log_service

def create_trade(db: Session, user_id: int, trade_in: TradeCreate) -> Trade:
    trade_data = trade_in.model_dump(exclude={"condition_checks"})
    new_trade = Trade(**trade_data, user_id=user_id)

    # Initialize empty rule violations (to be expanded when the rule engine is built)
    new_trade.rule_violations = {}

    db.add(new_trade)
    db.flush()

    for check_data in trade_in.condition_checks:
        new_check = TradeConditionCheck(**check_data.model_dump(), trade_id=new_trade.id)
        db.add(new_check)

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
