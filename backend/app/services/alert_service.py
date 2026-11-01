from sqlalchemy.orm import Session
from app.models.alert import Alert
import logging

logger = logging.getLogger(__name__)

def create_alert(db: Session, user_id: int, kind: str, message: str, trade_id: int = None):
    """
    Creates an actionable alert for the user (e.g., SL hit, Rule violated).
    """
    try:
        new_alert = Alert(
            user_id=user_id,
            trade_id=trade_id,
            kind=kind,
            message=message
        )
        db.add(new_alert)
        db.commit()
    except Exception as e:
        logger.error(f"Failed to create alert: {e}")
        db.rollback()
