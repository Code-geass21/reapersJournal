from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime

class LogOut(BaseModel):
    id: int
    ts: datetime
    level: str
    user_id: Optional[int] = None
    action: str
    entity_type: Optional[str] = None
    entity_id: Optional[int] = None
    before: Optional[Dict[str, Any]] = None
    after: Optional[Dict[str, Any]] = None
    source: str
    error_text: Optional[str] = None
    request_id: Optional[str] = None

    class Config:
        from_attributes = True
