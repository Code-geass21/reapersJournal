from decimal import Decimal
from app.models.alert import Alert

def test_closed_trade_edit_rejection(client, test_user_data):
    """Bug 86: Ensure normalized Decimals prevent editing core fields on closed trades."""
    # 1. Create a trade
    payload = {
        "strategy_id": test_user_data["strategy_id"],
        "instrument_id": test_user_data["instrument_id"],
        "direction": "long",
        "entry_price": 1.105,
        "size": 1.0
    }
    trade_res = client.post("/api/trades/", json=payload, headers=test_user_data["headers"])
    trade_id = trade_res.json()["id"]

    # 2. Close it
    client.put(
        f"/api/trades/{trade_id}",
        json={"direction": "long", "status": "closed", "exit_price": 1.110},
        headers=test_user_data["headers"]
    )

    # 3. Attempt to maliciously edit the entry price on the closed trade
    edit_payload = {"direction": "long", "entry_price": 1.106}
    bad_edit = client.put(f"/api/trades/{trade_id}", json=edit_payload, headers=test_user_data["headers"])

    assert bad_edit.status_code == 400
    assert "Cannot modify entry_price" in bad_edit.json()["detail"]

def test_dashboard_breakeven_counts(client, test_user_data):
    """Bugs 93 & 81: Ensure break-even trades are counted in the dashboard."""
    # 1. Create and close a trade at exact break-even
    trade_res = client.post("/api/trades/", json={
        "strategy_id": test_user_data["strategy_id"], "instrument_id": test_user_data["instrument_id"],
        "direction": "long", "entry_price": 100.0, "size": 1.0, "emotion": "calm"
    }, headers=test_user_data["headers"])

    client.put(f"/api/trades/{trade_res.json()['id']}", json={"direction": "long", "status": "closed", "exit_price": 100.0}, headers=test_user_data["headers"])

    # 2. Fetch dashboard
    dash_res = client.get("/api/dashboard/performance", headers=test_user_data["headers"])
    data = dash_res.json()

    assert data["total_trades"] >= 1
    # Check that emotion stats counted the break-even trade
    calm_stat = next((e for e in data["emotion_stats"] if e["name"].lower() == "calm"), None)
    assert calm_stat is not None
    assert calm_stat["trades"] >= 1
