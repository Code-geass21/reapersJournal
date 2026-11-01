from pydantic import BaseModel
from typing import List, Optional

class UserPreferenceBase(BaseModel):
    theme: str = "dark"
    default_strategy_ids: List[int] = []
    default_market: str = "FOREX"
    refresh_secs: int = 30

class UserPreferenceUpdate(BaseModel):
    theme: Optional[str] = None
    default_strategy_ids: Optional[List[int]] = None
    default_market: Optional[str] = None
    refresh_secs: Optional[int] = None

class UserPreferenceOut(UserPreferenceBase):
    user_id: int

    class Config:
        from_attributes = True
