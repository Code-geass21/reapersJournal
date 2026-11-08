from app.models.trade import Trade

def test_create_trade_with_sl_tp(client, db, test_user_data):
    """Checklist #1 (Bug 69): Create a trade WITH a stop loss and take profit."""
    payload = {
        "strategy_id": test_user_data["strategy_id"],
        "instrument_id": test_user_data["instrument_id"],
        "direction": "long",
        "entry_price": 1.1050,
        "size": 1.0,
        "stop_loss": 1.1000,
        "take_profit": 1.1150
    }

    response = client.post("/api/trades/", json=payload, headers=test_user_data["headers"])
    assert response.status_code == 200, f"Expected 200, got 500 crash. Detail: {response.text}"

    data = response.json()
    assert data["status"] == "open"

    # Verify the database directly to ensure initial_stop_loss was saved properly
    trade_id = data["id"]
    trade_db = db.query(Trade).filter(Trade.id == trade_id).first()
    assert float(trade_db.initial_stop_loss) == 1.1000

def test_edit_notes_and_strict_schema(client, test_user_data):
    """Checklist #2 & #3 (Bugs 70 & 71): Edit notes without crashing, reject bad directions."""

    # Setup: Create a quick naked trade
    payload = {
        "strategy_id": test_user_data["strategy_id"],
        "instrument_id": test_user_data["instrument_id"],
        "direction": "short",
        "entry_price": 140.50,
        "size": 0.5
    }
    create_res = client.post("/api/trades/", json=payload, headers=test_user_data["headers"])
    trade_id = create_res.json()["id"]

    # Test A (Bug 70): Edit only the notes (Partial Update)
    edit_payload = {"notes": "Testing a partial note update"}
    edit_res = client.put(f"/api/trades/{trade_id}", json=edit_payload, headers=test_user_data["headers"])

    assert edit_res.status_code == 200
    assert edit_res.json()["notes"] == "Testing a partial note update"

    # Test B (Bug 71): Catch invalid direction schema validation
    bad_payload = {"direction": "buy"} # Must be strictly 'long' or 'short'
    bad_res = client.put(f"/api/trades/{trade_id}", json=bad_payload, headers=test_user_data["headers"])

    assert bad_res.status_code == 422 # Pydantic Validation Error caught it successfully
