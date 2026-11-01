from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.orm import Session
import os
import uuid

from app.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.services import restore_service
from app.utils.security import verify_password

router = APIRouter(prefix="/restore", tags=["Restore"])
BACKUP_DIR = "/app/backups"

@router.post("/")
def restore_backup(
    password: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Validates the user's password, accepts a backup ZIP file, and triggers a full data restore.
    """
    if not file.filename.endswith('.zip'):
        raise HTTPException(status_code=400, detail="Only .zip backup files are allowed")

    # 1. Verify password for security
    if not verify_password(password, current_user.password_hash):
         raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect password. Restore aborted."
        )

    # 2. Save the uploaded ZIP file temporarily
    temp_zip_path = os.path.join(BACKUP_DIR, f"temp_restore_{uuid.uuid4().hex}.zip")
    try:
        with open(temp_zip_path, "wb") as buffer:
            buffer.write(file.file.read())

        # 3. Trigger the restore service
        restore_service.process_restore(db, current_user.id, temp_zip_path)

        return {"detail": "Restore completed successfully."}

    except Exception as e:
        # Clean up temp file on failure
        if os.path.exists(temp_zip_path):
            os.remove(temp_zip_path)
        raise HTTPException(status_code=500, detail=f"Restore failed: {str(e)}")
