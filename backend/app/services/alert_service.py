from sqlalchemy.orm import Session
from app.models.alert import Alert
import logging

logger = logging.getLogger(__name__)

def create_alert(db: Session, user_id: int, kind: str, message: str, trade_id: int = None) -> bool:
    try:
        if trade_id:
            base_msg = message.split(" at ")[0]

            existing = db.query(Alert).filter(
                Alert.trade_id == trade_id,
                Alert.kind == kind,
                Alert.message.startswith(base_msg)
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

        db.flush()
        return True
    except Exception as e:
        logger.error(f"Failed to create alert: {e}")
        return False
