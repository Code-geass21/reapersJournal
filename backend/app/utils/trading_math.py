from decimal import Decimal

def calculate_pips(direction: str, entry_price: float, exit_price: float, pip_size: float) -> float:
    entry = Decimal(str(entry_price))
    exit = Decimal(str(exit_price))
    pip_s = Decimal(str(pip_size))

    price_diff = (exit - entry) if direction == 'long' else (entry - exit)
    return float(price_diff / pip_s)

def calculate_quote_pnl(direction: str, entry_price: float, exit_price: float, size: float, contract_size: int) -> float:
    entry = Decimal(str(entry_price))
    exit = Decimal(str(exit_price))
    c_size = Decimal(str(contract_size))
    lot_size = Decimal(str(size))

    price_diff = (exit - entry) if direction == 'long' else (entry - exit)
    return float(price_diff * c_size * lot_size)

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
