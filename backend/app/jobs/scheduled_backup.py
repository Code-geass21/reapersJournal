import logging
import os
import shutil
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.user import User
from app.services import backup_service
from app.config import settings

logger = logging.getLogger(__name__)

# Track the last time a backup ran in memory so we only run it once a day
_last_backup_date = None

def run():
    """
    Checks if an automated backup is due, and generates a zip payload for the admin.
    """
    global _last_backup_date
    current_date = datetime.now(timezone.utc).date()

    if _last_backup_date == current_date:
        return # Backup already ran today

    db: Session = SessionLocal()
    try:
        # Find the admin user to attach the backup to
        admin = db.query(User).filter(User.role == 'admin').first()
        if not admin:
            return

        logger.info(f"Starting automated daily backup for admin user {admin.username}...")

        # We reuse the backup service which dumps to the mounted /app/backups volume
        zip_filepath = backup_service.create_user_backup(db, admin.id)

        # Optional: Housekeeping - Keep only the 7 most recent backups
        backup_dir = "/app/backups"
        if os.path.exists(backup_dir):
            files = sorted(
                [f for f in os.listdir(backup_dir) if f.endswith(".zip")],
                key=lambda f: os.path.getmtime(os.path.join(backup_dir, f)),
                reverse=True
            )
            # Remove older backups
            for old_file in files[7:]:
                try:
                    os.remove(os.path.join(backup_dir, old_file))
                    logger.info(f"Deleted old backup: {old_file}")
                except Exception as e:
                    logger.warning(f"Could not delete old backup {old_file}: {e}")

        _last_backup_date = current_date
        logger.info(f"Automated daily backup successful: {zip_filepath}")

    except Exception as e:
        logger.error(f"Failed to generate automated backup: {e}")
        raise e
    finally:
        db.close()
