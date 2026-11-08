import logging
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from app.models.app_log import AppLog

logger = logging.getLogger(__name__)

# FIX FOR BUG 32: Import the contextvar from main (delayed import to avoid circular dependency issues)
def get_current_request_id():
    try:
        from app.main import request_id_contextvar
        return request_id_contextvar.get()
    except Exception:
        return "unknown"

def write(
    db: Session,
    action: str,
    level: str = "INFO",
    user_id: int = None,
    entity_type: str = None,
    entity_id: int = None,
    before: dict = None,
    after: dict = None,
    source: str = "api",
    error_text: str = None,
    request_id: str = None
):
    """
    Centralized function to write to the master app_logs table.
    """
    try:
        # FIX FOR BUG 32: Grab the global request ID if one wasn't explicitly provided
        final_request_id = request_id if request_id else get_current_request_id()

        new_log = AppLog(
            level=level,
            user_id=user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            before=before,
            after=after,
            source=source,
            error_text=error_text,
            request_id=final_request_id
        )
        db.add(new_log)

        # FIX FOR BUG 33: Stop committing mid-transaction!
        # Use flush() to push the log to the DB within the current transaction.
        # If the caller's transaction rolls back (e.g., a trade deletion fails),
        # this log entry will safely roll back with it.
        db.flush()

    except Exception as e:
        logger.error(f"Failed to write to app_logs: {e}")


def prune_old_logs(db: Session, retention_days: int = 30) -> int:
    """FIX FOR BUG 64: Prevent app_logs from growing infinitely."""
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=retention_days)

    try:
        deleted_count = db.query(AppLog).filter(AppLog.ts < cutoff_date).delete()
        db.commit()
        return deleted_count
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to prune old logs: {e}")
        return 0
