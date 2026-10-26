from decimal import Decimal

def calculate_pnl(direction: str, entry_price: float, exit_price: float, size: float, instrument: dict) -> dict:
    """
    Calculates raw points (pips) and realized P&L based on the instrument specifications.
    Phase 1 implementation: Returns P&L in the quote currency of the instrument.
    """
    entry = Decimal(str(entry_price))
    exit = Decimal(str(exit_price))
    contract_size = Decimal(str(instrument['contract_size']))
    lot_size = Decimal(str(size))
    pip_size = Decimal(str(instrument['pip_size']))

    if direction == 'long':
        price_diff = exit - entry
    else: # short
        price_diff = entry - exit

    # Raw points/pips gained or lost
    pips = price_diff / pip_size

    # Realized P&L in quote currency
    pnl_realized = price_diff * contract_size * lot_size

    return {
        "pips": float(pips),
        "pnl_realized": float(pnl_realized)
    }

def calculate_r_multiple(direction: str, entry_price: float, exit_price: float, stop_loss: float) -> float:
    """
    Calculates the R-multiple (Risk multiple) of a closed trade.
    """
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
