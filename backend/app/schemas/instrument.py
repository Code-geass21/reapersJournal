from pydantic import BaseModel
from typing import Optional

class InstrumentBase(BaseModel):
    symbol: str
    provider_symbol: str
    market_code: str
    pip_size: float
    contract_size: int = 100000
    quote_ccy: str
    is_active: bool = True

class InstrumentCreate(InstrumentBase):
    pass

class InstrumentOut(InstrumentBase):
    id: int

    class Config:
        from_attributes = True
