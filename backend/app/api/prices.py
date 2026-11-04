from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.schemas.price import OpenTradePriceOut
from app.services import price_service

router = APIRouter(prefix="/prices", tags=["Prices"])

@router.get("/open", response_model=List[OpenTradePriceOut])
def get_open_trade_prices(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Returns cached prices and unrealized P&L for the user's open trades."""
    return price_service.get_open_trade_prices(db, current_user.id)
