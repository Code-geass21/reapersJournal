import os
import json
import zipfile
import shutil
import logging
from sqlalchemy.orm import Session
from app.utils.table_registry import BACKUP_REGISTRY

logger = logging.getLogger(__name__)

UPLOAD_DIR = "/app/uploads"
TEMP_DIR = "/app/backups/temp_restore"

def process_restore(db: Session, user_id: int, zip_filepath: str):
    if os.path.exists(TEMP_DIR):
        shutil.rmtree(TEMP_DIR)
    os.makedirs(TEMP_DIR, exist_ok=True)

    try:
        # 1. Unzip the file
        with zipfile.ZipFile(zip_filepath, 'r') as zip_ref:
            zip_ref.extractall(TEMP_DIR)

        # 2. Re-import JSON data
        # First, clear existing USER SPECIFIC data backwards
        for table_def in reversed(BACKUP_REGISTRY):
            # Skip users (they are logged in) and global tables (markets, instruments)
            if table_def["name"] in ["users", "markets", "instruments"]:
                continue

            query = db.query(table_def["model"])
            filtered_query = table_def["user_filter"](query, user_id)
            filtered_query.delete(synchronize_session=False)
        db.commit()

        # Then insert all data forwards
        for table_def in BACKUP_REGISTRY:
            if table_def["name"] == "users":
                continue

            json_file = os.path.join(TEMP_DIR, f"{table_def['name']}.json")
            if os.path.exists(json_file):
                with open(json_file, 'r') as f:
                    rows = json.load(f)
                    for row_data in rows:
                        # Ensure user_id matches the current user if it's a user-owned table
                        if 'user_id' in row_data:
                            row_data['user_id'] = user_id

                        # Use merge() instead of add() so we safely upsert global tables like Markets
                        new_record = table_def["model"](**row_data)
                        db.merge(new_record)
                db.commit()

        # 3. Restore image files to the uploads directory
        uploads_source = os.path.join(TEMP_DIR, "uploads")
        if os.path.exists(uploads_source):
            for filename in os.listdir(uploads_source):
                src = os.path.join(uploads_source, filename)
                dst = os.path.join(UPLOAD_DIR, filename)
                shutil.copy2(src, dst)

    except Exception as e:
        db.rollback()
        logger.error(f"Restore failed: {str(e)}")
        raise e
    finally:
        # Clean up
        if os.path.exists(TEMP_DIR):
            shutil.rmtree(TEMP_DIR)
        if os.path.exists(zip_filepath):
            os.remove(zip_filepath)
