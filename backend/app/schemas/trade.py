from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

class TradeConditionCheckBase(BaseModel):
    rule_id: int
    passed: bool
    note: Optional[str] = None

class TradeConditionCheckCreate(TradeConditionCheckBase):
    pass

class TradeConditionCheckOut(TradeConditionCheckBase):
    id: int
    trade_id: int
    created_at: datetime

    class Config:
        from_attributes = True

class TradeBase(BaseModel):
    strategy_id: int
    instrument_id: int
    direction: str  # 'long' or 'short'
    status: str = 'open'
    entry_price: float
    size: float
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    notes: Optional[str] = None
    tags: List[str] = []
    emotion: Optional[str] = None

class TradeCreate(TradeBase):
    condition_checks: List[TradeConditionCheckCreate] = []

class TradeUpdate(BaseModel):
    status: Optional[str] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    closed_at: Optional[datetime] = None
    exit_price: Optional[float] = None
    fees: Optional[float] = None
    notes: Optional[str] = None
    tags: Optional[List[str]] = None
    emotion: Optional[str] = None

class TradeOut(TradeBase):
    id: int
    user_id: int
    opened_at: datetime
    closed_at: Optional[datetime] = None
    exit_price: Optional[float] = None
    fees: float
    pnl_realized: Optional[float] = None
    r_multiple: Optional[float] = None
    rule_violations: Dict[str, Any] = {}
    condition_checks: List[TradeConditionCheckOut] = []

    class Config:
        from_attributes = True
