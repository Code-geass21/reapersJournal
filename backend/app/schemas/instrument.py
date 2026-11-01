from pydantic import BaseModel
from typing import Optional
from datetime import date

class InstrumentBase(BaseModel):
    symbol: str
    provider_symbol: str
    market_code: str
    pip_size: float
    contract_size: int = 100000
    quote_ccy: str

    # Phase 7: Optional derivative fields
    expiry: Optional[date] = None
    strike: Optional[float] = None
    option_type: Optional[str] = None

    is_active: bool = True

class InstrumentCreate(InstrumentBase):
    pass

class InstrumentOut(InstrumentBase):
    id: int

    class Config:
        from_attributes = True
