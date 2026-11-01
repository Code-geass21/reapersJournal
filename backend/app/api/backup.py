from fastapi import APIRouter, Depends, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
import os

from app.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.services import backup_service

router = APIRouter(prefix="/backup", tags=["Backup"])

def remove_file(path: str):
    """Utility to delete the zip file after it has been sent to the user."""
    try:
        if os.path.exists(path):
            os.remove(path)
    except Exception as e:
        print(f"Error removing temp backup file: {e}")

@router.get("/download")
def download_backup(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Generates a full JSON + Attachments backup ZIP for the current user
    and returns it as a downloadable file.
    """
    # Generate the ZIP file using the service
    zip_filepath = backup_service.create_user_backup(db, current_user.id)
    filename = os.path.basename(zip_filepath)

    # Schedule the physical file to be deleted from the server AFTER the download completes
    background_tasks.add_task(remove_file, zip_filepath)

    return FileResponse(
        path=zip_filepath,
        filename=filename,
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
