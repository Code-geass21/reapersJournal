import os
import shutil
import uuid
from fastapi import UploadFile, HTTPException
from sqlalchemy.orm import Session
from app.models.attachment import Attachment

UPLOAD_DIR = "/app/uploads"

# Ensure directory exists on startup
os.makedirs(UPLOAD_DIR, exist_ok=True)

def save_attachment(db: Session, file: UploadFile, user_id: int, owner_type: str, owner_id: int) -> Attachment:
    # Generate a unique filename to prevent collisions (e.g., two images named "chart.png")
    ext = os.path.splitext(file.filename)[1]
    unique_filename = f"{uuid.uuid4().hex}{ext}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)

    # Save the physical file to the Docker volume
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not save file to disk: {e}")

    # Create DB tracking record
    db_attachment = Attachment(
        user_id=user_id,
        owner_type=owner_type,
        owner_id=owner_id,
        path=unique_filename,
        mime=file.content_type,
        size=os.path.getsize(file_path)
    )

    db.add(db_attachment)
    db.commit()
    db.refresh(db_attachment)

    return db_attachment

def delete_attachment(db: Session, attachment: Attachment):
    # Remove physical file
    file_path = os.path.join(UPLOAD_DIR, attachment.path)
    if os.path.exists(file_path):
        os.remove(file_path)

    # Remove DB record
    db.delete(attachment)
    db.commit()
