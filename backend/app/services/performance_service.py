from sqlalchemy.orm import Session
from sqlalchemy import asc
from app.models.trade import Trade
from typing import List, Optional

def get_performance_stats(db: Session, user_id: int, strategy_ids: Optional[List[int]] = None):
    # Base query: only look at closed trades with a realized P&L
    query = db.query(Trade).filter(
        Trade.user_id == user_id,
        Trade.status == 'closed',
        Trade.pnl_realized.isnot(None)
    )

    if strategy_ids:
        query = query.filter(Trade.strategy_id.in_(strategy_ids))

    # Fetch ordered chronologically for the equity curve
    trades = query.order_by(asc(Trade.closed_at)).all()

    if not trades:
        return {
            "total_trades": 0,
            "win_rate": 0.0,
            "total_pnl": 0.0,
            "expectancy": 0.0,
            "profit_factor": 0.0,
            "equity_curve": []
        }

    winning_trades = [t for t in trades if t.pnl_realized > 0]
    losing_trades = [t for t in trades if t.pnl_realized < 0]

    total_trades = len(trades)
    win_rate = (len(winning_trades) / total_trades) * 100

    gross_profit = sum(float(t.pnl_realized) for t in winning_trades)
    gross_loss = abs(sum(float(t.pnl_realized) for t in losing_trades))
    total_pnl = gross_profit - gross_loss

    # Profit Factor
    if gross_loss > 0:
        profit_factor = gross_profit / gross_loss
    else:
        profit_factor = gross_profit if gross_profit > 0 else 0.0

    # Mathematical Expectancy = (Win % * Avg Win) - (Loss % * Avg Loss)
    avg_win = (gross_profit / len(winning_trades)) if winning_trades else 0
    avg_loss = (gross_loss / len(losing_trades)) if losing_trades else 0
    expectancy = ((win_rate / 100) * avg_win) - (((100 - win_rate) / 100) * avg_loss)

    # Calculate Cumulative Equity Curve
    equity_curve = []
    cumulative = 0.0
    for t in trades:
        cumulative += float(t.pnl_realized)
        date_str = t.closed_at.strftime("%Y-%m-%d %H:%M") if t.closed_at else ""
        equity_curve.append({
            "date": date_str,
            "cumulative_pnl": cumulative
        })

    return {
        "total_trades": total_trades,
        "win_rate": round(win_rate, 2),
        "total_pnl": round(total_pnl, 2),
        "expectancy": round(expectancy, 2),
        "profit_factor": round(profit_factor, 2),
        "equity_curve": equity_curve
    }
