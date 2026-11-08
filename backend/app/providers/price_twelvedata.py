# backend/app/providers/price_twelvedata.py

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

    for sym in unique_symbols:
        clean_sym = sym.replace('=X', '')
        if len(clean_sym) == 6:
            td_sym = f"{clean_sym[0:3]}/{clean_sym[3:6]}"
            formatted_symbols.append(td_sym)
            symbol_map[td_sym] = sym
        else:
            # FIX FOR BUG 58: Support raw symbols like BTC/USD or indices without assuming 6 chars
            formatted_symbols.append(clean_sym)
            symbol_map[clean_sym] = sym

    if not formatted_symbols:
        return {}

    batch_symbols = ",".join(formatted_symbols)

    # FIX FOR BUG 58: Hide API key from the base URL string.
    # Pass via params dictionary to avoid it leaking in log traces.
    url = "https://api.twelvedata.com/price"
    params = {
        "symbol": batch_symbols,
        "apikey": settings.twelvedata_api_key
    }

    try:
        # FIX FOR BUG 58: Add explicit 10 second timeout
        response = requests.get(url, params=params, timeout=10)

        # Handle 429 Quota Exceeded gracefully
        if response.status_code == 429:
            logger.warning("[TwelveData] Rate limit (429) reached. Try reducing refresh frequency.")
            return {}

        response.raise_for_status()
        data = response.json()

        if "status" in data and data["status"] == "error":
            # Redact the key just in case it is echoed in the provider message
            safe_msg = data.get('message', 'Unknown Error').replace(settings.twelvedata_api_key, '***REDACTED***')
            logger.error(f"TwelveData API Error: {safe_msg}")
            return {}

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

    except requests.exceptions.Timeout:
        logger.error("[TwelveData] API request timed out after 10 seconds.")
    except Exception as e:
        safe_error = str(e).replace(settings.twelvedata_api_key, '***REDACTED***')
        logger.error(f"[TwelveData] Failed to fetch prices: {safe_error}")

    return result
