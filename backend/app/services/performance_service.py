from sqlalchemy.orm import Session
from sqlalchemy import asc
from app.models.trade import Trade
from typing import List, Optional
from collections import defaultdict

def get_performance_stats(db: Session, user_id: int, strategy_ids: Optional[List[int]] = None):
    query = db.query(Trade).filter(
        Trade.user_id == user_id,
        Trade.status == 'closed',
        Trade.pnl_realized.isnot(None)
    )

    if strategy_ids:
        query = query.filter(Trade.strategy_id.in_(strategy_ids))

    trades = query.order_by(asc(Trade.closed_at)).all()

    if not trades:
        return {
            "total_trades": 0, "win_rate": 0.0, "total_pnl": 0.0,
            "expectancy": 0.0, "profit_factor": 0.0,
            "equity_curve": [], "emotion_stats": [], "tag_stats": []
        }

    winning_trades = [t for t in trades if t.pnl_realized > 0]
    losing_trades = [t for t in trades if t.pnl_realized < 0]

    total_trades = len(trades)
    win_rate = (len(winning_trades) / total_trades) * 100

    gross_profit = sum(float(t.pnl_realized) for t in winning_trades)
    gross_loss = abs(sum(float(t.pnl_realized) for t in losing_trades))
    total_pnl = gross_profit - gross_loss

    profit_factor = gross_profit / gross_loss if gross_loss > 0 else (gross_profit if gross_profit > 0 else 0.0)

    avg_win = (gross_profit / len(winning_trades)) if winning_trades else 0
    avg_loss = (gross_loss / len(losing_trades)) if losing_trades else 0
    expectancy = ((win_rate / 100) * avg_win) - (((100 - win_rate) / 100) * avg_loss)

    # Aggregations for charts
    equity_curve = []
    cumulative = 0.0

    emotion_data = defaultdict(lambda: {"wins": 0, "total": 0, "pnl": 0.0})
    tag_data = defaultdict(lambda: {"wins": 0, "total": 0, "pnl": 0.0})

    for t in trades:
        pnl = float(t.pnl_realized)
        is_win = 1 if pnl > 0 else 0

        # Equity Curve
        cumulative += pnl
        date_str = t.closed_at.strftime("%Y-%m-%d %H:%M") if t.closed_at else ""
        equity_curve.append({"date": date_str, "cumulative_pnl": cumulative})

        # Emotion aggregation
        if t.emotion:
            emotion_data[t.emotion]["total"] += 1
            emotion_data[t.emotion]["wins"] += is_win
            emotion_data[t.emotion]["pnl"] += pnl

        # Tag aggregation
        if t.tags:
            for tag in t.tags:
                tag_data[tag]["total"] += 1
                tag_data[tag]["wins"] += is_win
                tag_data[tag]["pnl"] += pnl

    # Format aggregates for Pydantic schema
    emotion_stats = [
        {"name": k.title(), "trades": v["total"], "win_rate": round((v["wins"] / v["total"]) * 100, 1), "pnl": round(v["pnl"], 2)}
        for k, v in emotion_data.items()
    ]
    tag_stats = [
        {"name": k, "trades": v["total"], "win_rate": round((v["wins"] / v["total"]) * 100, 1), "pnl": round(v["pnl"], 2)}
        for k, v in tag_data.items()
    ]

    # Sort by most profitable
    emotion_stats.sort(key=lambda x: x["pnl"], reverse=True)
    tag_stats.sort(key=lambda x: x["pnl"], reverse=True)

    return {
        "total_trades": total_trades,
        "win_rate": round(win_rate, 2),
        "total_pnl": round(total_pnl, 2),
        "expectancy": round(expectancy, 2),
        "profit_factor": round(profit_factor, 2),
        "equity_curve": equity_curve,
        "emotion_stats": emotion_stats,
        "tag_stats": tag_stats
    }
