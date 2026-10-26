from pydantic import BaseModel
from typing import Optional
from datetime import date

class StrategyBase(BaseModel):
    name: str
    description: Optional[str] = None
    market: str = "FOREX"
    funding_mode: str = "non_systematic"
    sip_amount: Optional[float] = None
    sip_frequency: Optional[str] = None
    start_date: Optional[date] = None
    is_active: bool = True

class StrategyCreate(StrategyBase):
    pass

class StrategyOut(StrategyBase):
    id: int
    user_id: int

    class Config:
        from_attributes = True
