import requests
import logging
from datetime import datetime, timedelta
import pytz

logger = logging.getLogger(__name__)

def fetch_upcoming_news():
    """Fetches this week's economic events from ForexFactory's public JSON."""
    try:
        url = "https://nfs.faireconomy.media/ff_calendar_thisweek.json"
        response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
        response.raise_for_status()
        events = response.json()

        now = datetime.utcnow()
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
        return upcoming[:5] # Return next 5 events

    except Exception as e:
        logger.error(f"[News] Failed to fetch ForexFactory data: {e}")
        return []
