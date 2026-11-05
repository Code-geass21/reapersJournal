from fastapi import APIRouter, Depends, UploadFile, File, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.schemas.user import UserOut
from app.services import user_service, attachment_service
from pydantic import BaseModel
from typing import List
from app.api.deps import get_admin_user
from app.utils.security import get_password_hash
from fastapi import HTTPException
from fastapi import APIRouter, Depends, UploadFile, File, Form, status
from app.utils.security import get_password_hash, verify_password


class AdminUserCreate(BaseModel):
    username: str
    email: str
    password: str
    role: str = "user"

class AdminUserUpdate(BaseModel):
    is_active: bool
    role: str

router = APIRouter(prefix="/users", tags=["Users"])

class ProfileUpdate(BaseModel):
    display_name: str

class PasswordUpdate(BaseModel):
    current_password: str
    new_password: str

@router.get("/me", response_model=UserOut)
def get_my_profile(current_user: User = Depends(get_current_user)):
    return current_user

@router.put("/me", response_model=UserOut)
def update_my_profile(
    profile_data: ProfileUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return user_service.update_profile(db, current_user, profile_data.display_name)

@router.put("/me/password")
def update_my_password(
    password_data: PasswordUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    user_service.update_password(
        db, current_user,
        password_data.current_password,
        password_data.new_password
    )
    return {"detail": "Password updated successfully"}

@router.post("/me/avatar", response_model=UserOut)
def upload_my_avatar(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Save physical file and DB attachment record
    attachment = attachment_service.save_attachment(
        db, file, current_user.id, owner_type="avatar", owner_id=current_user.id
    )

    # Link to user profile
    current_user.avatar_attachment_id = attachment.id
    db.commit()
    db.refresh(current_user)
    return current_user

@router.get("/", response_model=List[UserOut])
def get_all_users(db: Session = Depends(get_db), admin: User = Depends(get_admin_user)):
    """Admin only: List all users on the platform."""
    return db.query(User).order_by(User.id.asc()).all()

@router.post("/", response_model=UserOut)
def create_user_as_admin(
    user_in: AdminUserCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """Admin only: Manually provision a new user."""
    if db.query(User).filter((User.username == user_in.username) | (User.email == user_in.email)).first():
        raise HTTPException(status_code=400, detail="Username or email already exists")

    new_user = User(
        username=user_in.username,
        email=user_in.email,
        password_hash=get_password_hash(user_in.password),
        role=user_in.role
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@router.put("/{target_user_id}", response_model=UserOut)
def update_user_status(
    target_user_id: int,
    update_data: AdminUserUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """Admin only: Activate/deactivate or change roles of users."""
    if target_user_id == admin.id and not update_data.is_active:
        raise HTTPException(status_code=400, detail="You cannot disable your own admin account")

    user = db.query(User).filter(User.id == target_user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.is_active = update_data.is_active
    user.role = update_data.role
    db.commit()
    db.refresh(user)
    return user

# Update the endpoint signature to require a password
@router.delete("/{target_user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    target_user_id: int,
    password: str = Form(...), # Require admin password confirmation
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """Admin only: Permanently delete a user and all their data."""
    if target_user_id == admin.id:
        raise HTTPException(status_code=400, detail="You cannot delete your own admin account")

    # Verify the admin's password before executing the destructive action
    if not verify_password(password, admin.password_hash):
        raise HTTPException(status_code=401, detail="Incorrect admin password")

    target_user = db.query(User).filter(User.id == target_user_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")

    # FIX FOR BUG 25: Wipe all physical files owned by this user
    user_attachments = db.query(Attachment).filter(Attachment.user_id == target_user_id).all()
    for att in user_attachments:
        file_path = os.path.join(attachment_service.UPLOAD_DIR, att.path)
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception as e:
                print(f"Warning: Could not delete user file {file_path}: {e}")
        db.delete(att)

    # Log the deletion
    log_service.write(
        db, action="user.delete", user_id=admin.id,
        entity_type="user", entity_id=target_user_id,
        before={"username": target_user.username, "email": target_user.email}
    )

    db.delete(target_user)
    db.commit()
    return None
