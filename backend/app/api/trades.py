from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
import logging

from app.database import get_db
from app.models.trade import Trade
from app.schemas.trade import TradeCreate, TradeUpdate, TradeOut
from app.api.deps import get_current_user
from app.models.user import User
from app.services import trade_service
from app.jobs import fetch_prices, check_alerts
from app.services import log_service
from app.schemas.trade import TradeExecutionCreate

router = APIRouter(prefix="/trades", tags=["Trades"])
logger = logging.getLogger(__name__)

def trigger_background_price_and_alerts():
    """Helper function to run pricing and alerts sequentially in the background."""
    try:
        fetch_prices.run()
        check_alerts.run()
    except Exception as e:
        logger.error(f"Background price/alert trigger failed: {e}")

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
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # 1. Save the trade normally
    new_trade = trade_service.create_trade(db, current_user.id, trade_in)

    # 2. Fire the price check and alert engine immediately in the background
    background_tasks.add_task(trigger_background_price_and_alerts)

    return new_trade

@router.put("/{trade_id}", response_model=TradeOut)
def update_trade(
    trade_id: int,
    trade_in: TradeUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return trade_service.update_trade(db, current_user.id, trade_id, trade_in)


@router.delete("/{trade_id}", status_code=204)
def delete_trade(
    trade_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    trade = db.query(Trade).filter(Trade.id == trade_id, Trade.user_id == current_user.id).first()
    if not trade:
        raise HTTPException(status_code=404, detail="Trade not found")

    # Audit log the deletion
    log_service.write(
        db, action="trade.delete", user_id=current_user.id,
        entity_type="trade", entity_id=trade_id,
        before={"status": trade.status, "direction": trade.direction}
    )

    db.delete(trade)
    db.commit()
    return None

@router.post("/{trade_id}/executions", response_model=TradeOut)
def add_trade_execution(
    trade_id: int,
    exec_in: TradeExecutionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return trade_service.add_execution(db, current_user.id, trade_id, exec_in)
