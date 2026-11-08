from decimal import Decimal
from sqlalchemy.orm import Session
from app.models.price import PriceCache

from app.utils.trading_math import calculate_pips, calculate_quote_pnl, calculate_r_multiple

def get_usd_conversion_rate(db: Session, quote_ccy: str) -> Decimal:
    """Finds the exchange rate to convert the quote currency back to USD."""
    clean_ccy = quote_ccy.strip().upper()

    if clean_ccy == 'USD':
        return Decimal("1.0")

    # Check for USD as base currency (e.g., USDJPY)
    usd_base = db.query(PriceCache).filter(PriceCache.provider_symbol.like(f"USD{clean_ccy}%")).first()
    if usd_base and usd_base.price:
        return Decimal("1.0") / Decimal(str(usd_base.price))

    # Check for USD as quote currency (e.g., EURUSD)
    usd_quote = db.query(PriceCache).filter(PriceCache.provider_symbol.like(f"{clean_ccy}USD%")).first()
    if usd_quote and usd_quote.price:
        return Decimal(str(usd_quote.price))

    raise ValueError(f"Missing USD conversion rate for {clean_ccy}.")

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
        "fx_rate": float(conversion_rate)  # <-- Return rate used so it can be persisted
    }

__all__ = ['get_usd_conversion_rate', 'calculate_pnl', 'calculate_r_multiple']
