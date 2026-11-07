
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.news import NewsEvent
from app.schemas.dashboard import PerformanceStatsOut
from app.services import performance_service

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

@router.get("/performance", response_model=PerformanceStatsOut)
def get_performance(
    strategy_ids: Optional[str] = Query(None, description="Comma-separated strategy IDs"),
    start_date: Optional[str] = Query(None),  # <-- ADDED
    end_date: Optional[str] = Query(None),    # <-- ADDED
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    strat_ids = None

    if strategy_ids is not None:
        try:
            strat_ids = [
                int(sid.strip())
                for sid in strategy_ids.split(",")
                if sid.strip()
            ]

            if not strat_ids or any(sid <= 0 for sid in strat_ids):
                raise ValueError
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="strategy_ids must be comma-separated positive integers"
            )

    stats = performance_service.get_performance_stats(
        db,
        current_user.id,
        strat_ids,
        start_date,
        end_date
    )

    return stats


@router.get("/news")
def get_dashboard_news(db: Session = Depends(get_db)):
    """Returns the next 5 upcoming high/medium impact economic events."""

    now = datetime.now(timezone.utc)

    events = (
        db.query(NewsEvent)
        .filter(
            NewsEvent.event_time_utc > now,
            NewsEvent.impact.in_(["High", "Medium"])
        )
        .order_by(NewsEvent.event_time_utc.asc())
        .limit(5)
        .all()
    )

    return {
        "events": [
            {
                "title": e.title,
                "country": e.currency,
                "impact": e.impact,
                "time": e.event_time_utc.isoformat()
            }
            for e in events
        ]
    }
