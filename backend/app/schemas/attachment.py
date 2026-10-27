from pydantic import BaseModel
from datetime import datetime

class AttachmentOut(BaseModel):
    id: int
    user_id: int
    owner_type: str
    owner_id: int
    path: str
    mime: str
    size: int
    created_at: datetime

    class Config:
        from_attributes = True
