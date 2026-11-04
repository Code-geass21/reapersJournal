import requests
import logging
from datetime import datetime, timedelta
import pytz

logger = logging.getLogger(__name__)

# Simple memory cache to prevent 429 Too Many Requests errors
_news_cache = []
_last_fetch_time = None
CACHE_DURATION_HOURS = 1

def fetch_upcoming_news():
    """Fetches this week's economic events from ForexFactory's public JSON, with caching."""
    global _news_cache, _last_fetch_time

    now = datetime.utcnow()

    # Return cached data if it's less than 1 hour old
    if _last_fetch_time and _news_cache:
        time_since_fetch = now - _last_fetch_time
        if time_since_fetch < timedelta(hours=CACHE_DURATION_HOURS):
            logger.info("Returning cached ForexFactory news data.")
            # Filter the cached events to only show ones still in the future
            return [e for e in _news_cache if datetime.fromisoformat(e['time'].replace('Z', '')) > now]

    logger.info("Fetching fresh news data from ForexFactory...")
    try:
        url = "https://nfs.faireconomy.media/ff_calendar_thisweek.json"
        response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
        response.raise_for_status()
        events = response.json()

        # Look ahead 48 hours
        lookahead = now + timedelta(hours=48)

        upcoming = []
        for e in events:
            # ForexFactory provides dates in ISO format: 2026-10-28T08:30:00-04:00
            event_time = datetime.fromisoformat(e['date']).astimezone(pytz.utc).replace(tzinfo=None)

            # We only care about high impact ("High") or medium impact ("Medium") future events
            if now < event_time < lookahead and e['impact'] in ['High', 'Medium']:
                upcoming.append({
                    "title": e['title'],
                    "country": e['country'],
                    "impact": e['impact'],
                    "time": event_time.isoformat() + "Z"
                })

        # Sort by time
        upcoming.sort(key=lambda x: x['time'])

        # --- BUG 10 FIX: Stop aggressively truncating to 5 events ---
        # Cache and return all valid upcoming events to seed the DB properly
        _news_cache = upcoming
        _last_fetch_time = now

        return _news_cache

    except Exception as e:
        logger.error(f"[News] Failed to fetch ForexFactory data: {e}")
        # On error, return whatever we have in the cache, even if it's old
        return _news_cache
