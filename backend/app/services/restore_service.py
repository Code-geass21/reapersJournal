import os
import json
import zipfile
import shutil
from sqlalchemy.orm import Session
from app.utils.table_registry import BACKUP_REGISTRY

UPLOAD_DIR = "/app/uploads"
TEMP_DIR = "/app/backups/temp_restore"

def process_restore(db: Session, user_id: int, zip_filepath: str):
    """
    Unpacks a backup ZIP and restores the JSON data into the database for the given user,
    then copies the image attachments back into the uploads volume.
    """
    if os.path.exists(TEMP_DIR):
        shutil.rmtree(TEMP_DIR)
    os.makedirs(TEMP_DIR, exist_ok=True)

    try:
        # 1. Unzip the file
        with zipfile.ZipFile(zip_filepath, 'r') as zip_ref:
            zip_ref.extractall(TEMP_DIR)

        # 2. Re-import JSON data in topological order
        # We process the registry backwards to delete old child records before parents,
        # then process it forwards to insert parents before children.

        # Clear existing user data (Caution: This wipes their current journal)
        for table_def in reversed(BACKUP_REGISTRY):
            if table_def["name"] == "users":
                continue # Never delete the user account itself during a restore

            query = db.query(table_def["model"])
            filtered_query = table_def["user_filter"](query, user_id)
            filtered_query.delete(synchronize_session=False)
        db.commit()

        # Insert new data
        for table_def in BACKUP_REGISTRY:
            if table_def["name"] == "users":
                continue # Skip the user table; they are already logged in

            json_file = os.path.join(TEMP_DIR, f"{table_def['name']}.json")
            if os.path.exists(json_file):
                with open(json_file, 'r') as f:
                    rows = json.load(f)
                    for row_data in rows:
                        # Ensure user_id matches the current user (prevents malicious cross-account injection)
                        if 'user_id' in row_data:
                            row_data['user_id'] = user_id

                        new_record = table_def["model"](**row_data)
                        db.add(new_record)
                db.commit()

        # 3. Restore image files to the uploads directory
        uploads_source = os.path.join(TEMP_DIR, "uploads")
        if os.path.exists(uploads_source):
            for filename in os.listdir(uploads_source):
                src = os.path.join(uploads_source, filename)
                dst = os.path.join(UPLOAD_DIR, filename)
                shutil.copy2(src, dst)

    finally:
        # Clean up temp folder and the uploaded zip
        if os.path.exists(TEMP_DIR):
            shutil.rmtree(TEMP_DIR)
        if os.path.exists(zip_filepath):
            os.remove(zip_filepath)
