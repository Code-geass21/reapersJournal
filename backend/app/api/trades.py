from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models.trade import Trade, TradeConditionCheck
from app.schemas.trade import TradeCreate, TradeUpdate, TradeOut
from app.api.deps import get_current_user
from app.models.user import User

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

@router.post("/", response_model=TradeOut)
def create_trade(
    trade_in: TradeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    trade_data = trade_in.model_dump(exclude={"condition_checks"})
    new_trade = Trade(**trade_data, user_id=current_user.id)

    db.add(new_trade)
    db.flush() # Flush to get the new_trade.id

    for check_data in trade_in.condition_checks:
        new_check = TradeConditionCheck(**check_data.model_dump(), trade_id=new_trade.id)
        db.add(new_check)

    db.commit()
    db.refresh(new_trade)
    return new_trade
