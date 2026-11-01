from decimal import Decimal
from sqlalchemy.orm import Session
from app.models.price import PriceCache

def get_usd_conversion_rate(db: Session, quote_ccy: str) -> Decimal:
    """Finds the exchange rate to convert the quote currency back to USD."""

    # FIX: Strip whitespace to prevent database mismatch
    clean_ccy = quote_ccy.strip().upper()

    if clean_ccy == 'USD':
        return Decimal("1.0")

    # Check for USD/QuoteCCY (e.g. USDJPY=X). Rate is 1 / USDJPY
    usd_base = db.query(PriceCache).filter(PriceCache.provider_symbol.like(f"USD{clean_ccy}%")).first()
    if usd_base and usd_base.price:
        return Decimal("1.0") / Decimal(str(usd_base.price))

    # Check for QuoteCCY/USD (e.g. GBPUSD=X). Rate is GBPUSD
    usd_quote = db.query(PriceCache).filter(PriceCache.provider_symbol.like(f"{clean_ccy}USD%")).first()
    if usd_quote and usd_quote.price:
        return Decimal(str(usd_quote.price))

    # Fallback to 1 if no conversion rate is found in cache
    return Decimal("1.0")

def calculate_pnl(db: Session, direction: str, entry_price: float, exit_price: float, size: float, instrument: dict) -> dict:
    """
    Calculates raw points (pips) and realized P&L, auto-converting to USD.
    """
    entry = Decimal(str(entry_price))
    exit = Decimal(str(exit_price))
    contract_size = Decimal(str(instrument['contract_size']))
    lot_size = Decimal(str(size))
    pip_size = Decimal(str(instrument['pip_size']))

    # Safely get the quote currency, defaulting to USD if missing
    quote_ccy = instrument.get('quote_ccy', 'USD')

    if direction == 'long':
        price_diff = exit - entry
    else: # short
        price_diff = entry - exit

    # Raw points/pips gained or lost
    pips = price_diff / pip_size

    # Realized P&L in the pair's native quote currency
    pnl_quote_ccy = price_diff * contract_size * lot_size

    # Convert to USD account currency
    conversion_rate = get_usd_conversion_rate(db, quote_ccy)
    pnl_usd = pnl_quote_ccy * conversion_rate

    return {
        "pips": float(pips),
        "pnl_realized": float(pnl_usd)
    }

def calculate_r_multiple(direction: str, entry_price: float, exit_price: float, stop_loss: float) -> float:
    """Calculates the R-multiple (Risk multiple) of a closed trade."""
    if not stop_loss:
        return 0.0

    entry = Decimal(str(entry_price))
    exit = Decimal(str(exit_price))
    sl = Decimal(str(stop_loss))

    if direction == 'long':
        initial_risk = entry - sl
        if initial_risk <= 0: return 0.0
        profit = exit - entry
    else: # short
        initial_risk = sl - entry
        if initial_risk <= 0: return 0.0
        profit = entry - exit

    return float(profit / initial_risk)
