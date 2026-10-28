from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.schemas.dashboard import PerformanceStatsOut
from app.services import performance_service

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

@router.get("/performance", response_model=PerformanceStatsOut)
def get_performance(
    strategy_ids: Optional[str] = Query(None, description="Comma-separated strategy IDs"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    strat_ids = None
    if strategy_ids:
        try:
            # Parse "?strategy_ids=1,2,3" into a list of integers
            strat_ids = [int(sid.strip()) for sid in strategy_ids.split(",") if sid.strip()]
        except ValueError:
            pass

    stats = performance_service.get_performance_stats(db, current_user.id, strat_ids)
    return stats
