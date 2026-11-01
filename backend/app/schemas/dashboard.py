from pydantic import BaseModel
from typing import List

class EquityDataPoint(BaseModel):
    date: str
    cumulative_pnl: float

class CategoryStat(BaseModel):
    name: str
    pnl: float
    win_rate: float
    trades: int

class PerformanceStatsOut(BaseModel):
    total_trades: int
    win_rate: float
    total_pnl: float
    expectancy: float
    profit_factor: float
    equity_curve: List[EquityDataPoint]
    emotion_stats: List[CategoryStat] = []
    tag_stats: List[CategoryStat] = []
