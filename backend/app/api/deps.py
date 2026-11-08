from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlalchemy.orm import Session
from app.database import get_db
from app.config import settings
from app.models.user import User
from app.models.setting import AppSetting # FIX FOR BUG 35: Import setting model

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise credentials_exception

    # backend/app/api/deps.py (Snippet for get_current_user)

    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is disabled")

    # FIX FOR BUG 47: Compare JSONB boolean correctly to Python True
    maintenance_setting = db.query(AppSetting).filter(AppSetting.key == 'maintenance_mode').first()

    if maintenance_setting and maintenance_setting.value is True:
        # If maintenance is on, only admins can proceed
        if user.role != 'admin':
            raise HTTPException(
                status_code=503,
                detail="System is currently in maintenance mode. Please try again later."
            )

    return user

def get_admin_user(current_user: User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to perform this action"
        )
    return current_user
