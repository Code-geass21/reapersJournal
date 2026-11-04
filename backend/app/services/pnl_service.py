from decimal import Decimal
from sqlalchemy.orm import Session
from app.models.price import PriceCache

# Import the math we just moved
from app.utils.trading_math import calculate_pips, calculate_quote_pnl, calculate_r_multiple

def get_usd_conversion_rate(db: Session, quote_ccy: str) -> Decimal:
    """Finds the exchange rate to convert the quote currency back to USD."""
    clean_ccy = quote_ccy.strip().upper()

    if clean_ccy == 'USD':
        return Decimal("1.0")

    usd_base = db.query(PriceCache).filter(PriceCache.provider_symbol.like(f"USD{clean_ccy}%")).first()
    if usd_base and usd_base.price:
        return Decimal("1.0") / Decimal(str(usd_base.price))

    usd_quote = db.query(PriceCache).filter(PriceCache.provider_symbol.like(f"{clean_ccy}USD%")).first()
    if usd_quote and usd_quote.price:
        return Decimal(str(usd_quote.price))

    return Decimal("1.0")

def calculate_pnl(db: Session, direction: str, entry_price: float, exit_price: float, size: float, instrument: dict) -> dict:
    """Calculates raw points (pips) and realized P&L, auto-converting to USD."""

    # 1. Get raw values using the math utility
    pips = calculate_pips(direction, entry_price, exit_price, instrument['pip_size'])
    pnl_quote_ccy = calculate_quote_pnl(direction, entry_price, exit_price, size, instrument['contract_size'])

    # 2. Handle DB conversion
    quote_ccy = instrument.get('quote_ccy', 'USD')
    conversion_rate = get_usd_conversion_rate(db, quote_ccy)

    pnl_usd = Decimal(str(pnl_quote_ccy)) * conversion_rate

    return {
        "pips": pips,
        "pnl_realized": float(pnl_usd)
    }

# Ensure imports from other files don't break
__all__ = ['get_usd_conversion_rate', 'calculate_pnl', 'calculate_r_multiple']
