import yfinance as yf
from typing import Dict

def fetch_prices(symbols: list[str]) -> Dict[str, dict]:
    """
    Fetches current spot prices for a list of provider_symbols.
    Returns a dictionary mapping provider_symbol to price data.
    """
    if not symbols:
        return {}

    result = {}
    unique_symbols = list(set(symbols))

    # Initialize the batch yfinance Tickers object
    tickers = yf.Tickers(" ".join(unique_symbols))

    for symbol in unique_symbols:
        try:
            ticker = tickers.tickers[symbol]
            # .fast_info is a lightweight dict-like object for real-time spot prices
            current_price = ticker.fast_info.last_price

            if current_price:
                result[symbol] = {
                    "price": float(current_price),
                    "bid": None, # Unreliable on free-tier off-hours feeds
                    "ask": None,
                    "source": "yfinance"
                }
        except Exception as e:
            print(f"[yfinance Provider] Failed to fetch price for {symbol}: {e}")

    return result
