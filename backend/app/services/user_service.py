from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.user import User
from app.utils.security import get_password_hash, verify_password
from app.services import log_service

def update_profile(db: Session, user: User, display_name: str) -> User:
    before_state = {"display_name": user.display_name}
    user.display_name = display_name
    db.commit()
    db.refresh(user)

    log_service.write(
        db, action="user.update_profile", user_id=user.id,
        entity_type="user", entity_id=user.id,
        before=before_state, after={"display_name": display_name}
    )
    return user

def update_password(db: Session, user: User, current_password: str, new_password: str):
    if not verify_password(current_password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect current password"
        )

    user.password_hash = get_password_hash(new_password)
    db.commit()

    log_service.write(
        db, action="user.update_password", user_id=user.id,
        entity_type="user", entity_id=user.id
    )
