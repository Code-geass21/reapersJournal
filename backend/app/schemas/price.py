from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class OpenTradePriceOut(BaseModel):
    trade_id: int
    provider_symbol: str
    current_price: float
    unrealized_pips: float
    unrealized_pnl: float
    is_stale: bool
    fetched_at: datetime
