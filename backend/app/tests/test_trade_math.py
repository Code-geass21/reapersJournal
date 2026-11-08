from decimal import Decimal
from app.models.trade import Trade, TradeExecution

def test_partial_exit_and_ghost_lots(client, test_user_data):
    """Checklist #9 & #10 (Bug 50): Partial exits, Decimal math, auto-close on 0."""
    # 1. Create a 1.0 lot trade
    payload = {
        "strategy_id": test_user_data["strategy_id"],
        "instrument_id": test_user_data["instrument_id"],
        "direction": "long",
        "entry_price": 1.1000,
        "size": 1.0
    }
    create_res = client.post("/api/trades/", json=payload, headers=test_user_data["headers"])
    trade_id = create_res.json()["id"]

    # 2. Scale out exactly half (0.5 lots)
    exit_1 = client.post(
        f"/api/trades/{trade_id}/executions",
        json={"execution_type": "exit", "price": 1.1050, "size": 0.5},
        headers=test_user_data["headers"]
    )
    assert exit_1.status_code == 200
    assert exit_1.json()["status"] == "open"
    assert exit_1.json()["pnl_realized"] > 0

    # 3. Try to exit 0.501 lots (Tests the Decimal('0.01') quantization fix)
    # The backend should cleanly round this to 0.50 and perfectly liquidate the trade.
    exit_2 = client.post(
        f"/api/trades/{trade_id}/executions",
        json={"execution_type": "exit", "price": 1.1100, "size": 0.501},
        headers=test_user_data["headers"]
    )
    assert exit_2.status_code == 200
    assert exit_2.json()["status"] == "closed"


def test_historical_fx_rate_lock(client, test_user_data):
    """Checklist #7 (Bug 72): Ensure editing notes doesn't re-price history."""
    # 1. Create an open trade
    payload = {
        "strategy_id": test_user_data["strategy_id"],
        "instrument_id": test_user_data["instrument_id"],
        "direction": "short",
        "entry_price": 150.00,
        "size": 1.0
    }
    trade_res = client.post("/api/trades/", json=payload, headers=test_user_data["headers"])
    trade_id = trade_res.json()["id"]

    # 2. Close it to lock in the P&L and the current FX rate
    close_res = client.put(
        f"/api/trades/{trade_id}",
        json={"direction": "short", "status": "closed", "exit_price": 149.00},
        headers=test_user_data["headers"]
    )
    assert close_res.status_code == 200
    original_pnl = close_res.json()["pnl_realized"]

    # 3. Edit notes (This triggers _recalculate_trade_metrics in the backend)
    # Because we added the exchange_rate column to trade_executions,
    # it should pull the historical rate instead of fetching a live one.
    edit_res = client.put(
        f"/api/trades/{trade_id}",
        json={"direction": "short", "notes": "Testing FX lock"},
        headers=test_user_data["headers"]
    )

    assert edit_res.status_code == 200
    assert edit_res.json()["pnl_realized"] == original_pnl
