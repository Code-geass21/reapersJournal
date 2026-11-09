import logging
from sqlalchemy.orm import Session
from app.models.alert import Alert

logger = logging.getLogger(__name__)

def create_alert(db: Session, user_id: int, kind: str, message: str, trade_id: int = None) -> bool:
    try:
        if trade_id:
            # FIX FOR BUG 87: Dedupe by EXACT message across ALL statuses.
            # If a user dismisses "SL hit at 1.105", it stays quiet.
            # If they edit the trade and move SL to 1.100, the message changes, allowing a new alert.
            existing = db.query(Alert).filter(
                Alert.trade_id == trade_id,
                Alert.kind == kind,
                Alert.message == message
            ).first()

            if existing:
                return False

        # FIX FOR BUG 92: Use a SAVEPOINT (begin_nested) so if the alert insert fails,
        # it does not roll back the parent transaction (like creating a trade).
        with db.begin_nested():
            new_alert = Alert(
                user_id=user_id,
                trade_id=trade_id,
                kind=kind,
                message=message
            )
            db.add(new_alert)

        # Flush to DB, but let the parent caller handle the final commit()
        db.flush()
        return True

    except Exception as e:
        logger.error(f"Failed to create alert: {e}")
        # db.begin_nested() automatically rolls back its own scope on exception,
        # so we safely return False without breaking the main transaction.
        return False
