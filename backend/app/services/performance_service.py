from sqlalchemy.orm import Session
from sqlalchemy import asc, func
from app.models.trade import Trade
from typing import List, Optional
from collections import defaultdict
from app.models.strategy import Strategy, StrategyDeposit
from datetime import datetime
from fastapi import HTTPException

def get_performance_stats(
    db: Session,
    user_id: int,
    strategy_ids: Optional[List[int]] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
):
    # FIX FOR BUGS 93 & 81: Only compute stats on fully closed trades,
    # but include break-evens (removed the pnl_realized != 0 filter).
    query = db.query(Trade).filter(
        Trade.user_id == user_id,
        Trade.status == 'closed',
        Trade.pnl_realized.isnot(None)
    )

    dep_query = db.query(StrategyDeposit).join(Strategy).filter(Strategy.user_id == user_id)

    if strategy_ids:
        query = query.filter(Trade.strategy_id.in_(strategy_ids))
        dep_query = dep_query.filter(StrategyDeposit.strategy_id.in_(strategy_ids))

    # Apply date filters with explicit 400 validation
    if start_date:
        try:
            dt_start = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            # FIX FOR BUG 80: Filter by closed_at instead of opened_at
            query = query.filter(Trade.closed_at >= dt_start)
            dep_query = dep_query.filter(StrategyDeposit.date >= dt_start.date())
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid start_date format")

    if end_date:
        try:
            dt_end = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            query = query.filter(Trade.closed_at <= dt_end)
            dep_query = dep_query.filter(StrategyDeposit.date <= dt_end.date())
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid end_date format")

    # FIX FOR BUG 80: Order by closed_at (fallback to updated_at for partials) for an accurate chronological equity curve
    trades = query.order_by(asc(func.coalesce(Trade.closed_at, Trade.updated_at))).all()
    deposits = dep_query.all()

    net_funding = sum(float(d.amount) if d.kind == 'deposit' else -float(d.amount) for d in deposits)

    if not trades:
        return {
            "net_funding": net_funding, "total_trades": 0, "win_rate": 0.0,
            "total_pnl": 0.0, "expectancy": 0.0, "profit_factor": None,
            "max_drawdown": 0.0, "equity_curve": [], "emotion_stats": [], "tag_stats": []
        }

    winning_trades = [t for t in trades if float(t.pnl_realized) > 0]
    losing_trades = [t for t in trades if float(t.pnl_realized) < 0]

    total_trades = len(trades)

    # FIX FOR BUG 60: Win rate ignores break-evens (they dilute it otherwise)
    resolved_trades = len(winning_trades) + len(losing_trades)
    win_rate = (len(winning_trades) / resolved_trades * 100) if resolved_trades > 0 else 0.0

    gross_profit = sum(float(t.pnl_realized) for t in winning_trades)
    gross_loss = abs(sum(float(t.pnl_realized) for t in losing_trades))
    total_pnl = gross_profit - gross_loss

    # FIX FOR BUG 60: Profit factor handles 0 losses correctly (None = infinity)
    profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else (None if gross_profit > 0 else 0.0)

    avg_win = (gross_profit / len(winning_trades)) if winning_trades else 0
    avg_loss = (gross_loss / len(losing_trades)) if losing_trades else 0
    expectancy = ((win_rate / 100) * avg_win) - (((100 - win_rate) / 100) * avg_loss)

    # Aggregations for charts & Drawdown
    equity_curve = []
    cumulative = 0.0
    peak = 0.0
    max_drawdown = 0.0

    emotion_data = defaultdict(lambda: {"wins": 0, "total": 0, "pnl": 0.0})
    tag_data = defaultdict(lambda: {"wins": 0, "total": 0, "pnl": 0.0})

    for t in trades:
        pnl = float(t.pnl_realized)
        is_win = 1 if pnl > 0 else 0

        # Equity Curve & Drawdown
        cumulative += pnl
        if cumulative > peak:
            peak = cumulative

        drawdown = peak - cumulative
        if drawdown > max_drawdown:
            max_drawdown = drawdown

        # Use closed_at if available, else updated_at
        dt = t.closed_at or t.updated_at
        date_str = dt.strftime("%Y-%m-%d %H:%M") if dt else ""
        equity_curve.append({"date": date_str, "cumulative_pnl": cumulative})

        # FIX FOR BUG 81: Count ALL closed trades (including break-evens) in total counts
        if t.emotion:
            emotion_data[t.emotion]["total"] += 1
            emotion_data[t.emotion]["wins"] += is_win
            emotion_data[t.emotion]["pnl"] += pnl

        if t.tags:
            for tag in t.tags:
                tag_data[tag]["total"] += 1
                tag_data[tag]["wins"] += is_win
                tag_data[tag]["pnl"] += pnl

    emotion_stats = [
        {"name": k.title(), "trades": v["total"], "win_rate": round((v["wins"] / v["total"]) * 100, 1) if v["total"] > 0 else 0.0, "pnl": round(v["pnl"], 2)}
        for k, v in emotion_data.items()
    ]
    tag_stats = [
        {"name": k, "trades": v["total"], "win_rate": round((v["wins"] / v["total"]) * 100, 1) if v["total"] > 0 else 0.0, "pnl": round(v["pnl"], 2)}
        for k, v in tag_data.items()
    ]

    emotion_stats.sort(key=lambda x: x["pnl"], reverse=True)
    tag_stats.sort(key=lambda x: x["pnl"], reverse=True)

    return {
        "net_funding": round(net_funding, 2),
        "total_trades": total_trades,
        "win_rate": round(win_rate, 2),
        "total_pnl": round(total_pnl, 2),
        "expectancy": round(expectancy, 2),
        "profit_factor": round(profit_factor, 2) if profit_factor is not None else None,
        "max_drawdown": round(max_drawdown, 2),
        "equity_curve": equity_curve,
        "emotion_stats": emotion_stats,
        "tag_stats": tag_stats
    }
