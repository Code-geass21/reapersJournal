from typing import Optional
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.services import news_service
from app.api.deps import get_current_user
from app.models.user import User

router = APIRouter(prefix="/news", tags=["News"])

@router.get("/upcoming")
def get_upcoming_news(
    impact: Optional[str] = None,
    currency: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)  # Protects endpoint with auth
):
    """Fetches upcoming economic events, optionally filtered by impact or currency."""
    return news_service.get_upcoming_news(db, impact, currency)
