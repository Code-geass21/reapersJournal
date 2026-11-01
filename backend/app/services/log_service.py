from sqlalchemy.orm import Session
from app.models.app_log import AppLog
import logging

logger = logging.getLogger(__name__)

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
            request_id=request_id
        )
        db.add(new_log)
        db.commit()
    except Exception as e:
        logger.error(f"Failed to write to app_logs: {e}")
        db.rollback()
