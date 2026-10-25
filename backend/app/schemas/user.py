from pydantic import BaseModel, EmailStr, Field
from typing import Optional

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    # Enforce bcrypt's 72-byte limit before it hits the hashing utility
    password: str = Field(..., max_length=72)

class UserOut(BaseModel):
    id: int
    username: str
    email: EmailStr
    role: str
    display_name: Optional[str] = None
    is_active: bool

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str
