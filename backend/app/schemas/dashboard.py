from pydantic import BaseModel
from typing import List

class EquityDataPoint(BaseModel):
    date: str
    cumulative_pnl: float

class PerformanceStatsOut(BaseModel):
    total_trades: int
    win_rate: float
    total_pnl: float
    expectancy: float
    profit_factor: float
    equity_curve: List[EquityDataPoint]
