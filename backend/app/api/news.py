from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.services import news_service

router = APIRouter(prefix="/news", tags=["News"])

@router.get("/upcoming")
def get_upcoming_news(
    impact: Optional[str] = None,
    currency: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Fetches upcoming economic events, optionally filtered by impact or currency."""
    return news_service.get_upcoming_news(db, impact, currency)
