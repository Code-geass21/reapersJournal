from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime, timezone
from app.database import get_db
from app.models.news import NewsEvent

router = APIRouter(prefix="/news", tags=["News"])

@router.get("/upcoming")
def get_upcoming_news(
    impact: Optional[str] = None,
    currency: Optional[str] = None,
    db: Session = Depends(get_db)
):
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
