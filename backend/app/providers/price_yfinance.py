import yfinance as yf
from typing import Dict
import logging

logger = logging.getLogger(__name__)

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
            current_price = None

            # Attempt 1: Try fast_info (fastest, but sometimes brittle)
            try:
                current_price = ticker.fast_info.last_price
            except Exception as fast_info_error:
                logger.debug(f"fast_info failed for {symbol}: {fast_info_error}")

            # Attempt 2: Fallback to history (slower, but more reliable)
            if current_price is None:
                history = ticker.history(period="1d")
                if not history.empty:
                    # Get the most recent closing price
                    current_price = history['Close'].iloc[-1]

            if current_price:
                result[symbol] = {
                    "price": float(current_price),
                    "bid": None, # Unreliable on free-tier off-hours feeds
                    "ask": None,
                    "source": "yfinance"
                }
            else:
                logger.warning(f"Could not retrieve price data for {symbol} via any method.")

        except Exception as e:
            logger.error(f"[yfinance Provider] Failed to fetch price for {symbol}: {e}")

    return result
