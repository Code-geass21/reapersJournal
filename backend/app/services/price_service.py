from sqlalchemy.orm import Session
from datetime import datetime, timezone
from typing import List, Dict, Any

from app.models.trade import Trade
from app.models.instrument import Instrument
from app.models.price import PriceCache
from app.services import pnl_service
from app.config import settings

def get_open_trade_prices(db: Session, user_id: int) -> List[Dict[str, Any]]:
    """Calculates cached prices, unrealized P&L, and staleness for a user's open trades."""
    open_trades = db.query(Trade, Instrument).join(
        Instrument, Trade.instrument_id == Instrument.id
    ).filter(
        Trade.user_id == user_id,
        Trade.status == 'open'
    ).all()

    results = []
    now = datetime.now(timezone.utc)
    stale_threshold_seconds = settings.price_refresh_secs * 3

    for trade, instrument in open_trades:
        cached = db.query(PriceCache).filter(PriceCache.provider_symbol == instrument.provider_symbol).first()

        if not cached or cached.price is None:
            continue

        current_price = float(cached.price)

        # Calculate staleness
        fetched_at_utc = cached.fetched_at.replace(tzinfo=timezone.utc) if cached.fetched_at.tzinfo is None else cached.fetched_at
        age_seconds = (now - fetched_at_utc).total_seconds()
        is_stale = age_seconds > stale_threshold_seconds

        # Calculate unrealized P&L
        inst_dict = {"contract_size": instrument.contract_size, "pip_size": instrument.pip_size, "quote_ccy": instrument.quote_ccy}
        pnl_data = pnl_service.calculate_pnl(
            db=db,
            direction=trade.direction,
            entry_price=float(trade.entry_price),
            exit_price=current_price,
            size=float(trade.size),
            instrument=inst_dict
        )

        results.append({
            "trade_id": trade.id,
            "provider_symbol": instrument.provider_symbol,
            "current_price": current_price,
            "unrealized_pips": pnl_data['pips'],
            "unrealized_pnl": pnl_data['pnl_realized'],
            "is_stale": is_stale,
            "fetched_at": fetched_at_utc,
            "stale_threshold_secs": stale_threshold_seconds
        })

    return results
