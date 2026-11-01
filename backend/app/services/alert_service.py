from sqlalchemy.orm import Session
from app.models.alert import Alert
import logging

logger = logging.getLogger(__name__)

def create_alert(db: Session, user_id: int, kind: str, message: str, trade_id: int = None) -> bool:
    """
    Creates an actionable alert for the user. Returns True if created, False if a duplicate is already pending.
    """
    try:
        # Prevent spamming the same alert if the user hasn't dismissed the previous one
        if trade_id:
            existing = db.query(Alert).filter(
                Alert.trade_id == trade_id,
                Alert.kind == kind,
                Alert.status.in_(['new', 'seen'])
            ).first()

            if existing:
                return False

        new_alert = Alert(
            user_id=user_id,
            trade_id=trade_id,
            kind=kind,
            message=message
        )
        db.add(new_alert)
        db.commit()
        return True
    except Exception as e:
        logger.error(f"Failed to create alert: {e}")
        db.rollback()
        return False
