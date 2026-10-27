from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List
import os
from app.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.attachment import Attachment
from app.schemas.attachment import AttachmentOut
from app.services import attachment_service

router = APIRouter(prefix="/attachments", tags=["Attachments"])

@router.post("/", response_model=AttachmentOut)
def upload_attachment(
    owner_type: str = Form(...),
    owner_id: int = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if owner_type not in ['trade', 'avatar']:
        raise HTTPException(status_code=400, detail="Invalid owner type. Must be 'trade' or 'avatar'")

    attachment = attachment_service.save_attachment(db, file, current_user.id, owner_type, owner_id)
    return attachment

@router.get("/trade/{trade_id}", response_model=List[AttachmentOut])
def get_trade_attachments(
    trade_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return db.query(Attachment).filter(
        Attachment.owner_type == 'trade',
        Attachment.owner_id == trade_id,
        Attachment.user_id == current_user.id
    ).order_by(Attachment.created_at.desc()).all()

@router.get("/{attachment_id}/file")
def get_attachment_file(
    attachment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    attachment = db.query(Attachment).filter(Attachment.id == attachment_id).first()
    if not attachment:
        raise HTTPException(status_code=404, detail="Attachment not found")

    if current_user.role != 'admin' and attachment.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to view this file")

    file_path = os.path.join(attachment_service.UPLOAD_DIR, attachment.path)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File missing from disk")

    return FileResponse(file_path, media_type=attachment.mime)

@router.delete("/{attachment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_attachment(
    attachment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    attachment = db.query(Attachment).filter(
        Attachment.id == attachment_id,
        Attachment.user_id == current_user.id
    ).first()

    if not attachment:
        raise HTTPException(status_code=404, detail="Attachment not found")

    attachment_service.delete_attachment(db, attachment)
    return None
