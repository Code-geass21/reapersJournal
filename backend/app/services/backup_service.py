import os
import json
import shutil
import zipfile
from datetime import datetime, date
from decimal import Decimal
from sqlalchemy.orm import Session
from app.utils.table_registry import BACKUP_REGISTRY
from app.models.attachment import Attachment

BACKUP_DIR = "/app/backups"
UPLOAD_DIR = "/app/uploads"

# Ensure the Docker volume mount point exists
os.makedirs(BACKUP_DIR, exist_ok=True)

def custom_serializer(obj):
    """Handles serialization for Dates, Datetimes, and Decimals."""
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError(f"Type {type(obj)} not serializable")

def create_user_backup(db: Session, user_id: int) -> str:
    """Exports user data to JSON and bundles it with attachments in a ZIP file."""
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    backup_name = f"reapers_journal_backup_user_{user_id}_{timestamp}"
    temp_dir = os.path.join(BACKUP_DIR, backup_name)
    os.makedirs(temp_dir, exist_ok=True)

    try:
        # 1. Export Data to JSON using the Registry Contract
        for table_def in BACKUP_REGISTRY:
            query = db.query(table_def["model"])
            filtered_query = table_def["user_filter"](query, user_id)
            rows = filtered_query.all()

            # Convert SQLAlchemy objects to raw dictionaries
            data = []
            for row in rows:
                row_dict = {c.name: getattr(row, c.name) for c in row.__table__.columns}
                data.append(row_dict)

            file_path = os.path.join(temp_dir, f"{table_def['name']}.json")
            with open(file_path, "w") as f:
                json.dump(data, f, default=custom_serializer, indent=2)

        # 2. Package Physical Attachments (Screenshots)
        attachments = db.query(Attachment).filter(Attachment.user_id == user_id).all()
        if attachments:
            attachments_dir = os.path.join(temp_dir, "uploads")
            os.makedirs(attachments_dir, exist_ok=True)
            for att in attachments:
                src_path = os.path.join(UPLOAD_DIR, att.path)
                if os.path.exists(src_path):
                    shutil.copy2(src_path, os.path.join(attachments_dir, att.path))

        # 3. Create the ZIP Archive
        zip_filename = f"{backup_name}.zip"
        zip_filepath = os.path.join(BACKUP_DIR, zip_filename)

        with zipfile.ZipFile(zip_filepath, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(temp_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    # Archive path must be relative so the zip doesn't contain the full Linux path
                    arcname = os.path.relpath(file_path, temp_dir)
                    zipf.write(file_path, arcname)

        return zip_filepath

    finally:
        # 4. Clean up the uncompressed temporary folder
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
