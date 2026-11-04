from sqlalchemy.orm import Session
from datetime import datetime, timezone
from typing import Optional, List
from app.models.news import NewsEvent

def get_upcoming_news(db: Session, impact: Optional[str] = None, currency: Optional[str] = None) -> List[dict]:
    """Queries the database for upcoming economic events based on filters."""
    query = db.query(NewsEvent).filter(NewsEvent.event_time_utc > datetime.now(timezone.utc))

    if impact:
        query = query.filter(NewsEvent.impact == impact)
    if currency:
        query = query.filter(NewsEvent.currency == currency)

    events = query.order_by(NewsEvent.event_time_utc.asc()).all()

    return [{
        "title": e.title,
        "country": e.currency,
        "impact": e.impact,
        "time": e.event_time_utc.isoformat()
    } for e in events]
