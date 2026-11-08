import time  # <-- Required for cache expiration checks
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlalchemy.orm import Session

from app.database import get_db
from app.config import settings
from app.models.user import User
from app.models.setting import AppSetting  # FIX FOR BUG 35: Import setting model

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

# FIX FOR BUG 66: Simple in-memory cache to save 1 query per API request
_maintenance_cache = {"is_active": False, "expires_at": 0}

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

    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is disabled")

    # FIX FOR BUG 66: Use cached maintenance setting if not expired
    global _maintenance_cache
    current_time = time.time()

    if current_time > _maintenance_cache["expires_at"]:
        setting = db.query(AppSetting).filter(AppSetting.key == 'maintenance_mode').first()
        _maintenance_cache["is_active"] = setting and setting.value is True
        _maintenance_cache["expires_at"] = current_time + 60.0  # Cache for 60 seconds

    if _maintenance_cache["is_active"] and user.role != 'admin':
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
