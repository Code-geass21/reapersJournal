from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserOut, Token
from app.utils.security import get_password_hash, verify_password, create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES
from datetime import timedelta
from app.models.setting import AppSetting

router = APIRouter(prefix="/auth", tags=["Auth"])


# backend/app/api/auth.py (Snippet for register)

@router.post("/register", response_model=UserOut)
def register(user_in: UserCreate, db: Session = Depends(get_db)):
    # FIX FOR BUG 35 & 47: Enforce global registration lock properly
    registration_setting = db.query(AppSetting).filter(
        AppSetting.key == 'allow_registration'
    ).first()

    is_first_user = db.query(User).count() == 0

    # JSONB 'false' deserializes to Python False, not a string
    allow_reg = (registration_setting and registration_setting.value is True)

    if not is_first_user and not allow_reg:
        raise HTTPException(status_code=403, detail="Open registration is disabled. Contact an administrator.")

    if db.query(User).filter(User.username == user_in.username).first() or \
       db.query(User).filter(User.email == user_in.email).first():
        raise HTTPException(status_code=400, detail="Username or email already registered")

    # FIX FOR BUG 48: Only the very first user becomes an admin
    assigned_role = "admin" if is_first_user else "user"

    new_user = User(
        username=user_in.username,
        email=user_in.email,
        password_hash=get_password_hash(user_in.password),
        role=assigned_role
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is disabled")

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username, "role": user.role}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}
