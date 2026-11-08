from decimal import Decimal
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from app.models.price import PriceCache
from app.config import settings

from app.utils.trading_math import calculate_pips, calculate_quote_pnl, calculate_r_multiple

def get_usd_conversion_rate(db: Session, quote_ccy: str) -> Decimal:
    """Finds the exchange rate to convert the quote currency back to USD."""
    clean_ccy = quote_ccy.strip().upper()

    if clean_ccy == 'USD':
        return Decimal("1.0")

    # Helper to check age
    now = datetime.now(timezone.utc)
    stale_threshold_seconds = settings.price_refresh_secs * 3

    def is_rate_valid(cached_price: PriceCache) -> bool:
        if not cached_price or not cached_price.price:
            return False
        # FIX FOR BUG 46: Reject rates older than 3x interval
        fetched_at_utc = cached_price.fetched_at.replace(tzinfo=timezone.utc) if cached_price.fetched_at.tzinfo is None else cached_price.fetched_at
        age_seconds = (now - fetched_at_utc).total_seconds()
        return age_seconds <= stale_threshold_seconds

    # Check for USD as base currency (e.g., USDJPY)
    usd_base = db.query(PriceCache).filter(PriceCache.provider_symbol.like(f"USD{clean_ccy}%")).first()
    if is_rate_valid(usd_base):
        return Decimal("1.0") / Decimal(str(usd_base.price))

    # Check for USD as quote currency (e.g., EURUSD)
    usd_quote = db.query(PriceCache).filter(PriceCache.provider_symbol.like(f"{clean_ccy}USD%")).first()
    if is_rate_valid(usd_quote):
        return Decimal(str(usd_quote.price))

    raise ValueError(f"Missing or stale USD conversion rate for {clean_ccy}.")

def calculate_pnl(db: Session, direction: str, entry_price: float, exit_price: float, size: float, instrument: dict, force_fx_rate: Decimal = None) -> dict:
    """Calculates raw points (pips) and realized P&L, auto-converting to USD."""
    pips = calculate_pips(direction, entry_price, exit_price, instrument['pip_size'])
    pnl_quote_ccy = calculate_quote_pnl(direction, entry_price, exit_price, size, instrument['contract_size'])

    quote_ccy = instrument.get('quote_ccy', 'USD')

    # FIX FOR BUG 72: Use the forced historical rate if provided, otherwise fetch live
    conversion_rate = force_fx_rate if force_fx_rate is not None else get_usd_conversion_rate(db, quote_ccy)

    pnl_usd = Decimal(str(pnl_quote_ccy)) * conversion_rate

    return {
        "pips": pips,
        "pnl_realized": float(pnl_usd),
        "fx_rate": float(conversion_rate)  # Return rate used so it can be persisted
    }

__all__ = ['get_usd_conversion_rate', 'calculate_pnl', 'calculate_r_multiple']
