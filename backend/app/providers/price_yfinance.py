import logging
import math
from typing import Dict, Any
import requests

import yfinance as yf

logger = logging.getLogger(__name__)

# 1. Create a custom session to spoof a real web browser
session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
})

def _valid_price(value: Any) -> float | None:
    """Convert a candidate price to a finite float."""
    if value is None:
        return None

    try:
        price = float(value)
    except (TypeError, ValueError, OverflowError):
        return None

    if not math.isfinite(price) or price <= 0:
        return None

    return price

def fetch_prices(symbols: list[str]) -> Dict[str, dict]:
    """
    Fetch prices for Yahoo Finance symbols.

    Returns:
        A mapping of symbol to price data for successful lookups.
        Symbols with unavailable prices are omitted.
    """
    result: Dict[str, dict] = {}

    # Remove duplicates while preserving input order.
    unique_symbols = list(dict.fromkeys(
        symbol.strip() for symbol in symbols if symbol.strip()
    ))

    for symbol in unique_symbols:
        try:
            # 2. Pass the custom session into the yfinance Ticker!
            ticker = yf.Ticker(symbol, session=session)
            current_price = None

            # Attempt 1: Yahoo Finance fast_info.
            try:
                current_price = _valid_price(
                    ticker.fast_info.last_price
                )
            except Exception as exc:
                logger.debug(
                    "fast_info failed for %s: %s",
                    symbol,
                    exc,
                )

            # Attempt 2: Recent daily history.
            if current_price is None:
                try:
                    history = ticker.history(
                        period="5d",
                        interval="1d",
                    )

                    if not history.empty and "Close" in history.columns:
                        current_price = _valid_price(
                            history["Close"].dropna().iloc[-1]
                            if not history["Close"].dropna().empty
                            else None
                        )

                except Exception as exc:
                    logger.warning(
                        "History lookup failed for %s: %s",
                        symbol,
                        exc,
                    )

            if current_price is None:
                logger.warning(
                    "No valid price available for %s",
                    symbol,
                )
                continue

            result[symbol] = {
                "price": current_price,
                "bid": None,
                "ask": None,
                "source": "yfinance",
            }

            logger.info(
                "Retrieved price for %s: %s",
                symbol,
                current_price,
            )

        except Exception:
            logger.exception(
                "Unexpected error fetching price for %s",
                symbol,
            )

    return result
