from fastapi import APIRouter, Depends, Body
from sqlalchemy.orm import Session
from app.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.schemas.user import UserOut
from app.services import user_service
from pydantic import BaseModel

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
