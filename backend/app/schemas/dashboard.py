from pydantic import BaseModel
from typing import List, Optional

class EquityDataPoint(BaseModel):
    date: str
    cumulative_pnl: float

class CategoryStat(BaseModel):
    name: str
    pnl: float
    win_rate: float
    trades: int

class PerformanceStatsOut(BaseModel):
    net_funding: float           # <-- ADDED
    total_trades: int
    win_rate: float
    total_pnl: float
    expectancy: float
    profit_factor: Optional[float] = None  # <-- CHANGED TO OPTIONAL
    max_drawdown: float          # <-- ADDED
    equity_curve: List[EquityDataPoint]
    emotion_stats: List[CategoryStat] = []
    tag_stats: List[CategoryStat] = []
