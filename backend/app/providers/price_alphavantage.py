import requests
import logging
from typing import Dict
from app.config import settings

logger = logging.getLogger(__name__)

def fetch_prices(symbols: list[str]) -> Dict[str, dict]:
    """Fetches spot prices for Forex pairs using Alpha Vantage."""
    if not symbols:
        return {}

    if not settings.alpha_vantage_api_key:
        logger.error("Alpha Vantage API key is missing from environment.")
        return {}

    result = {}
    unique_symbols = list(set(symbols))

    for symbol in unique_symbols:
        # Clean the symbol from DB format (e.g., 'EURUSD=X' -> 'EURUSD')
        clean_symbol = symbol.replace('=X', '')

        if len(clean_symbol) != 6:
            logger.warning(f"Symbol '{symbol}' does not match expected 6-character format.")
            continue

        base_currency = clean_symbol[0:3]
        quote_currency = clean_symbol[3:6]

        url = f"https://www.alphavantage.co/query?function=CURRENCY_EXCHANGE_RATE&from_currency={base_currency}&to_currency={quote_currency}&apikey={settings.alpha_vantage_api_key}"

        try:
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()

            if "Realtime Currency Exchange Rate" in data:
                rate_data = data["Realtime Currency Exchange Rate"]

                result[symbol] = {
                    "price": float(rate_data["5. Exchange Rate"]),
                    "bid": float(rate_data["8. Bid Price"]),
                    "ask": float(rate_data["9. Ask Price"]),
                    "source": "alphavantage"
                }
                logger.info(f"Successfully fetched Alpha Vantage price for {symbol}")
            elif "Note" in data or "Information" in data:
                 logger.warning(f"Alpha Vantage API limit/note: {data}")
            else:
                 logger.warning(f"Unexpected response for {symbol}: {data}")

        except Exception as e:
            logger.error(f"[AlphaVantage] Failed to fetch price for {symbol}: {e}")

    return result
