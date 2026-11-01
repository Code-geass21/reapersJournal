from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.preference import UserPreference
from app.schemas.setting import UserPreferenceOut, UserPreferenceUpdate

router = APIRouter(prefix="/settings", tags=["Settings"])

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
