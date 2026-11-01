from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.app_log import AppLog
from app.schemas.log import LogOut

router = APIRouter(prefix="/logs", tags=["Logs"])

@router.get("/", response_model=List[LogOut])
def get_logs(
    level: Optional[str] = None,
    entity_type: Optional[str] = None,
    limit: int = Query(100, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(AppLog)

    # Security: Normal users only see their own logs. Admins see everything.
    if current_user.role != 'admin':
        query = query.filter(AppLog.user_id == current_user.id)

    if level:
        query = query.filter(AppLog.level == level)
    if entity_type:
        query = query.filter(AppLog.entity_type == entity_type)

    # Return newest logs first
    return query.order_by(AppLog.ts.desc()).limit(limit).all()
