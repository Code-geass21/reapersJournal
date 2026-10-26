from pydantic import BaseModel
from typing import Optional

class InstrumentBase(BaseModel):
    symbol: str
    provider_symbol: str
    market_code: str
    pip_size: float
    contract_size: int
    quote_ccy: str
    is_active: bool = True

class InstrumentOut(InstrumentBase):
    id: int

    class Config:
        from_attributes = True
