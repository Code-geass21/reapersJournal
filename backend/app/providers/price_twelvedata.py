import requests
import logging
from typing import Dict
from app.config import settings

logger = logging.getLogger(__name__)

def fetch_prices(symbols: list[str]) -> Dict[str, dict]:
    if not symbols:
        return {}

    if not settings.twelvedata_api_key:
        logger.error("TwelveData API key is missing from environment.")
        return {}

    result = {}
    unique_symbols = list(set(symbols))
    formatted_symbols = []
    symbol_map = {}

    # Map 'EURUSD=X' to 'EUR/USD'
    for sym in unique_symbols:
        clean_sym = sym.replace('=X', '')
        if len(clean_sym) == 6:
            td_sym = f"{clean_sym[0:3]}/{clean_sym[3:6]}"
            formatted_symbols.append(td_sym)
            symbol_map[td_sym] = sym

    if not formatted_symbols:
        return {}

    # Join symbols into a single batch request
    batch_symbols = ",".join(formatted_symbols)
    url = f"https://api.twelvedata.com/price?symbol={batch_symbols}&apikey={settings.twelvedata_api_key}"

    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        if "status" in data and data["status"] == "error":
            logger.error(f"TwelveData API Error: {data['message']}")
            return {}

        # TwelveData returns a different JSON structure for 1 symbol vs multiple
        if len(formatted_symbols) == 1:
            td_sym = formatted_symbols[0]
            orig_sym = symbol_map[td_sym]
            if "price" in data:
                result[orig_sym] = {
                    "price": float(data["price"]),
                    "bid": None,
                    "ask": None,
                    "source": "twelvedata"
                }
                logger.info(f"Successfully fetched TwelveData price for {orig_sym}")
        else:
            for td_sym, price_data in data.items():
                orig_sym = symbol_map.get(td_sym)
                if orig_sym and "price" in price_data:
                    result[orig_sym] = {
                        "price": float(price_data["price"]),
                        "bid": None,
                        "ask": None,
                        "source": "twelvedata"
                    }
                    logger.info(f"Successfully fetched TwelveData price for {orig_sym}")

    except Exception as e:
        logger.error(f"[TwelveData] Failed to fetch prices: {e}")

    return result
