from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, timezone
import math

from app.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.trade import Trade
from app.models.instrument import Instrument
from app.models.price import PriceCache
from app.schemas.price import OpenTradePriceOut
from app.services import pnl_service
from app.config import settings

router = APIRouter(prefix="/prices", tags=["Prices"])

@router.get("/open", response_model=List[OpenTradePriceOut])
def get_open_trade_prices(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Get all open trades for this user with their instrument data
    open_trades = db.query(Trade, Instrument).join(
        Instrument, Trade.instrument_id == Instrument.id
    ).filter(
        Trade.user_id == current_user.id,
        Trade.status == 'open'
    ).all()

    results = []
    now = datetime.now(timezone.utc)

    # 3x the refresh interval is considered stale data
    stale_threshold_seconds = settings.price_refresh_secs * 3

    for trade, instrument in open_trades:
        # Check the cache for this symbol
        cached = db.query(PriceCache).filter(PriceCache.provider_symbol == instrument.provider_symbol).first()

        if not cached or cached.price is None:
            continue

        current_price = float(cached.price)

        # Calculate staleness
        fetched_at_utc = cached.fetched_at.replace(tzinfo=timezone.utc) if cached.fetched_at.tzinfo is None else cached.fetched_at
        age_seconds = (now - fetched_at_utc).total_seconds()
        is_stale = age_seconds > stale_threshold_seconds

        # Use existing service to calculate unrealized P&L
        inst_dict = {"contract_size": instrument.contract_size, "pip_size": instrument.pip_size}
        pnl_data = pnl_service.calculate_pnl(
            direction=trade.direction,
            entry_price=trade.entry_price,
            exit_price=current_price,
            size=trade.size,
            instrument=inst_dict
        )

        results.append({
            "trade_id": trade.id,
            "provider_symbol": instrument.provider_symbol,
            "current_price": current_price,
            "unrealized_pips": pnl_data['pips'],
            "unrealized_pnl": pnl_data['pnl_realized'],
            "is_stale": is_stale,
            "fetched_at": fetched_at_utc
        })

    return results
