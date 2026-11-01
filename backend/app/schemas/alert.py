from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class AlertBase(BaseModel):
    kind: str
    message: str
    status: str
    trade_id: Optional[int] = None

class AlertOut(AlertBase):
    id: int
    user_id: int
    created_at: datetime

    class Config:
        from_attributes = True
