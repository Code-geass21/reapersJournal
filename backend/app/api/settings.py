from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Any, List, Optional
from sqlalchemy.orm import Session
from app.database import get_db
from app.api.deps import get_current_user, get_admin_user
from app.models.user import User
from app.models.preference import UserPreference
from app.schemas.setting import UserPreferenceOut, UserPreferenceUpdate
from app.models.setting import AppSetting

router = APIRouter(prefix="/settings", tags=["Settings"])

class AppSettingUpdate(BaseModel):
    value: Any

class AppSettingOut(BaseModel):
    key: str
    value: Any
    description: Optional[str] = None

    class Config:
        from_attributes = True


@router.get("/global", response_model=List[AppSettingOut])
def get_global_settings(
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    return db.query(AppSetting).order_by(AppSetting.key.asc()).all()

@router.put("/global/{key}", response_model=AppSettingOut)
def update_global_setting(
    key: str,
    setting_in: AppSettingUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    setting = db.query(AppSetting).filter(AppSetting.key == key).first()
    if not setting:
        raise HTTPException(status_code=404, detail="Setting not found")

    # FIX FOR BUG 84: Validate specific types per key to prevent bad JSON injections
    if key in ['maintenance_mode', 'allow_registration']:
        if not isinstance(setting_in.value, bool):
            raise HTTPException(status_code=400, detail=f"{key} must be a boolean.")
    elif key == 'price_provider':
        if setting_in.value not in ['twelvedata', 'alphavantage']:
            raise HTTPException(status_code=400, detail="Invalid price provider.")

    setting.value = setting_in.value
    db.commit()
    db.refresh(setting)
    return setting


@router.get("/preferences", response_model=UserPreferenceOut)
def get_preferences(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    prefs = db.query(UserPreference).filter(UserPreference.user_id == current_user.id).first()

    # Auto-initialize defaults if they don't exist yet
    if not prefs:
        prefs = UserPreference(user_id=current_user.id)
        db.add(prefs)
        db.commit()
        db.refresh(prefs)

    return prefs

@router.put("/preferences", response_model=UserPreferenceOut)
def update_preferences(
    prefs_in: UserPreferenceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    prefs = db.query(UserPreference).filter(UserPreference.user_id == current_user.id).first()

    if not prefs:
        prefs = UserPreference(user_id=current_user.id)
        db.add(prefs)

    update_data = prefs_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(prefs, key, value)

    db.commit()
    db.refresh(prefs)
    return prefs
