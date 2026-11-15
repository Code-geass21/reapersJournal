import logging
from sqlalchemy.orm import Session
from app.models.alert import Alert

logger = logging.getLogger(__name__)

def create_alert(db: Session, user_id: int, kind: str, message: str, trade_id: int = None) -> bool:
    try:
        if trade_id:
            # FIX FOR BUGS 87 & 94: Dedupe based on the static trigger level, not the live price.
            # Example message: "Stop Loss (1.105) hit for EURUSD at 1.104"
            # We split at " at " to extract just "Stop Loss (1.105) hit for EURUSD"
            base_msg = message.split(" at ")[0]

            # Drop the status filter. This ensures that even if an alert is 'dismissed',
            # we don't recreate it unless the user actually changed their SL/TP level.
            existing = db.query(Alert).filter(
                Alert.trade_id == trade_id,
                Alert.kind == kind,
                Alert.message.startswith(base_msg)
            ).first()

            if existing:
                return False

        # FIX FOR BUG 92: Use a SAVEPOINT (begin_nested) to prevent rolling back parent trades
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
        # db.begin_nested() automatically rolls back its own scope on exception
        return False
