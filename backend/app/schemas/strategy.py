from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import date

# --- Strategy Rule Schemas ---
class StrategyRuleBase(BaseModel):
    rule_type: str # 'entry', 'exit', 'risk', 'filter'
    label: str
    params: Dict[str, Any] = Field(default_factory=dict)
    is_required: bool = True
    sort_order: int = 0

class StrategyRuleCreate(StrategyRuleBase):
    pass

class StrategyRuleOut(StrategyRuleBase):
    id: int
    strategy_id: int

    class Config:
        from_attributes = True

# --- Existing Strategy Schemas ---
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

# --- Strategy Deposit Schemas ---
class StrategyDepositBase(BaseModel):
    amount: float
    kind: str  # 'deposit' or 'withdrawal'
    date: date
    note: Optional[str] = None

class StrategyDepositCreate(StrategyDepositBase):
    pass

class StrategyDepositOut(StrategyDepositBase):
    id: int
    strategy_id: int

    class Config:
        from_attributes = True
