from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
from app.database import get_db
from app.models.trade import Trade, TradeConditionCheck
from app.models.instrument import Instrument
from app.schemas.trade import TradeCreate, TradeUpdate, TradeOut
from app.api.deps import get_current_user
from app.models.user import User
from app.services import pnl_service # <-- Import the new service

router = APIRouter(prefix="/trades", tags=["Trades"])

@router.get("/", response_model=List[TradeOut])
def get_trades(
    strategy_id: int = None,
    status: str = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Trade).filter(Trade.user_id == current_user.id)
    if strategy_id:
        query = query.filter(Trade.strategy_id == strategy_id)
    if status:
         query = query.filter(Trade.status == status)
    return query.order_by(Trade.opened_at.desc()).all()

@router.get("/{trade_id}", response_model=TradeOut)
def get_trade(
    trade_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    trade = db.query(Trade).filter(Trade.id == trade_id, Trade.user_id == current_user.id).first()
    if not trade:
        raise HTTPException(status_code=404, detail="Trade not found")
    return trade

@router.post("/", response_model=TradeOut)
def create_trade(
    trade_in: TradeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    trade_data = trade_in.model_dump(exclude={"condition_checks"})
    new_trade = Trade(**trade_data, user_id=current_user.id)

    db.add(new_trade)
    db.flush()

    for check_data in trade_in.condition_checks:
        new_check = TradeConditionCheck(**check_data.model_dump(), trade_id=new_trade.id)
        db.add(new_check)

    db.commit()
    db.refresh(new_trade)
    return new_trade

@router.put("/{trade_id}", response_model=TradeOut)
def update_trade(
    trade_id: int,
    trade_in: TradeUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    trade = db.query(Trade).filter(Trade.id == trade_id, Trade.user_id == current_user.id).first()
    if not trade:
        raise HTTPException(status_code=404, detail="Trade not found")

    update_data = trade_in.model_dump(exclude_unset=True)

    # Check if this update is closing the trade
    if trade.status == 'open' and update_data.get('status') == 'closed':
        if not update_data.get('exit_price'):
            raise HTTPException(status_code=400, detail="Exit price is required to close a trade")

        instrument = db.query(Instrument).filter(Instrument.id == trade.instrument_id).first()
        inst_dict = {"contract_size": instrument.contract_size, "pip_size": instrument.pip_size}

        # Calculate P&L
        pnl_data = pnl_service.calculate_pnl(
            direction=trade.direction,
            entry_price=trade.entry_price,
            exit_price=update_data['exit_price'],
            size=trade.size,
            instrument=inst_dict
        )
        update_data['pnl_realized'] = pnl_data['pnl_realized']

        # Calculate R-Multiple
        if trade.stop_loss:
            update_data['r_multiple'] = pnl_service.calculate_r_multiple(
                direction=trade.direction,
                entry_price=trade.entry_price,
                exit_price=update_data['exit_price'],
                stop_loss=trade.stop_loss
            )

        if not update_data.get('closed_at'):
            update_data['closed_at'] = datetime.utcnow()

    # Apply updates
    for key, value in update_data.items():
        setattr(trade, key, value)

    db.commit()
    db.refresh(trade)
    return trade
