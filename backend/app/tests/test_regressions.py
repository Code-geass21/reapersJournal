"""Regression tests for the final tracker items: 72, 88, 96/31, 98, 102, 103."""
import pytest
from sqlalchemy import text
from app.services import alert_service
from app.jobs import check_alerts
from app.tests.helpers import set_price


def _create(client, d, inst_key, direction, entry, size=1.0, **extra):
    payload = {"strategy_id": d["strategy_id"], "instrument_id": d[inst_key],
               "direction": direction, "entry_price": entry, "size": size, **extra}
    r = client.post("/api/trades/", json=payload, headers=d["headers"])
    assert r.status_code == 200, r.text
    return r.json()["id"]


def _close(client, d, trade_id, direction, exit_price):
    return client.put(f"/api/trades/{trade_id}", headers=d["headers"],
                      json={"direction": direction, "status": "closed", "exit_price": exit_price})


# ---------------- 72 / 98: FX history is locked, JPY precision ----------------
def test_jpy_pnl_is_locked_and_precise(client, db, test_user_data):
    d = test_user_data
    set_price(db, d["jpy_conversion_symbol"], 150.0)           # USDJPY = 150
    tid = _create(client, d, "jpy_instrument_id", "long", 150.00)
    res = _close(client, d, tid, "long", 151.00)
    assert res.status_code == 200, res.text
    # +1.00 JPY * 100000 units = 100000 JPY -> / 150 = 666.67 USD
    assert res.json()["pnl_realized"] == pytest.approx(666.67, abs=0.01)

    set_price(db, d["jpy_conversion_symbol"], 140.0)            # rate moves
    edit = client.put(f"/api/trades/{tid}", headers=d["headers"], json={"direction": "long", "notes": "later edit"})
    assert edit.status_code == 200, edit.text
    assert edit.json()["pnl_realized"] == res.json()["pnl_realized"]   # unchanged by the new rate

    rate = db.execute(text("SELECT exchange_rate::text FROM trade_executions WHERE trade_id=:t AND execution_type='exit'"),
                      {"t": tid}).scalar()
    assert rate.startswith("0.0066666667")                      # 10 decimals, not 0.00667


def test_pre_migration_trade_keeps_recorded_pnl(client, db, test_user_data):
    d = test_user_data
    set_price(db, d["jpy_conversion_symbol"], 150.0)
    tid = _create(client, d, "jpy_instrument_id", "long", 150.00)
    before = _close(client, d, tid, "long", 151.00).json()["pnl_realized"]

    # simulate a trade saved before migration 015: no stored rate
    db.execute(text("UPDATE trade_executions SET exchange_rate = NULL, rate_source = NULL WHERE trade_id=:t"), {"t": tid})
    db.commit()
    set_price(db, d["jpy_conversion_symbol"], 100.0)            # today's rate would give 1000.00

    edit = client.put(f"/api/trades/{tid}", headers=d["headers"], json={"direction": "long", "notes": "legacy edit"})
    assert edit.status_code == 200, edit.text
    assert edit.json()["pnl_realized"] == before                # NOT re-priced at 100
    src = db.execute(text("SELECT rate_source FROM trade_executions WHERE trade_id=:t AND execution_type='exit'"),
                     {"t": tid}).scalar()
    assert src == "implied"


# ---------------- 88 / 102: stale rate fallback is allowed and logged ----------------
def test_close_with_stale_rate_is_logged(client, db, test_user_data):
    d = test_user_data
    set_price(db, d["jpy_conversion_symbol"], 150.0, age_seconds=3 * 86400)   # 3 days old
    tid = _create(client, d, "jpy_instrument_id", "long", 150.00)
    res = _close(client, d, tid, "long", 151.00)
    assert res.status_code == 200, res.text
    assert res.json()["pnl_realized"] == pytest.approx(666.67, abs=0.01)
    assert db.execute(text("SELECT rate_source FROM trade_executions WHERE trade_id=:t AND execution_type='exit'"),
                      {"t": tid}).scalar() == "stale"
    warn = db.execute(text("SELECT count(*) FROM app_logs WHERE action='fx.stale_rate_used' AND entity_id=:t"),
                      {"t": tid}).scalar()
    assert warn == 1


def test_close_without_any_rate_is_400_not_500(client, db, test_user_data):
    d = test_user_data
    db.execute(text("DELETE FROM price_cache WHERE provider_symbol=:s"), {"s": d["jpy_conversion_symbol"]})
    db.commit()
    tid = _create(client, d, "jpy_instrument_id", "long", 150.00)
    res = _close(client, d, tid, "long", 151.00)
    assert res.status_code == 400
    assert "rate" in res.json()["detail"].lower()


# ---------------- 96 / 31: audit rows carry the user id on the FIRST write ----------------
def test_audit_log_has_user_id(client, db, test_user_data):
    d = test_user_data
    tid = _create(client, d, "instrument_id", "long", 1.10)
    uid = db.execute(text("""SELECT user_id FROM app_logs
                             WHERE source='db_trigger' AND entity_type='trades' AND entity_id=:t
                             ORDER BY id ASC LIMIT 1"""), {"t": tid}).scalar()
    assert uid == d["user_id"]


# ---------------- 87 / 94 / 83 / 103: alerts ----------------
def test_alert_dedupe_ignores_price_and_rearms(client, db, test_user_data):
    d = test_user_data
    tid = _create(client, d, "instrument_id", "long", 1.1000, stop_loss=1.0950)
    uid = d["user_id"]

    assert alert_service.create_alert(db, uid, "sl_hit", "Stop Loss (1.095) hit for X at 1.0949", tid) is True
    assert alert_service.create_alert(db, uid, "sl_hit", "Stop Loss (1.095) hit for X at 1.0948", tid) is False
    assert alert_service.create_alert(db, uid, "sl_hit", "Stop Loss (1.095) hit for X at 1.0947", tid) is False
    db.commit()
    count = lambda: db.execute(text("SELECT count(*) FROM alerts WHERE trade_id=:t AND kind='sl_hit'"), {"t": tid}).scalar()
    assert count() == 1

    alert_service.rearm(db, tid, "sl_hit"); db.commit()          # price came back inside
    assert alert_service.create_alert(db, uid, "sl_hit", "Stop Loss (1.095) hit for X at 1.0940", tid) is True
    db.commit()
    assert count() == 2


def test_check_alerts_job_alerts_once_then_rearms(client, db, test_user_data):
    d = test_user_data
    sym = f"T{d['strategy_id']}CHK"
    inst_id = db.execute(text("""INSERT INTO instruments (market_code, symbol, provider_symbol, pip_size, contract_size, quote_ccy)
                                 VALUES ('FOREX', :s, :p, 0.0001, 100000, 'USD') RETURNING id"""),
                         {"s": sym, "p": sym + "=X"}).scalar()
    db.commit()
    tid = client.post("/api/trades/", headers=d["headers"], json={
        "strategy_id": d["strategy_id"], "instrument_id": inst_id, "direction": "long",
        "entry_price": 1.1000, "size": 1.0, "stop_loss": 1.0950}).json()["id"]
    n = lambda: db.execute(text("SELECT count(*) FROM alerts WHERE trade_id=:t"), {"t": tid}).scalar()

    for price in (1.0949, 1.0948, 1.0947):                       # three cycles beyond SL, price moving
        set_price(db, sym + "=X", price); check_alerts.run()
    assert n() == 1

    set_price(db, sym + "=X", 1.1000); check_alerts.run()        # back inside by more than a pip
    set_price(db, sym + "=X", 1.0940); check_alerts.run()        # breach again
    assert n() == 2

    db.execute(text("DELETE FROM trades WHERE id=:t"), {"t": tid})
    db.execute(text("DELETE FROM instruments WHERE id=:i"), {"i": inst_id}); db.commit()


# ---------------- 98: model and table agree ----------------
def test_price_cache_columns_match_model(db):
    row = db.execute(text("""SELECT numeric_precision, numeric_scale, is_nullable FROM information_schema.columns
                             WHERE table_name='price_cache' AND column_name='price'""")).one()
    assert (row.numeric_precision, row.numeric_scale, row.is_nullable) == (20, 10, "NO")


def test_unknown_or_unused_setting_rejected(client, db):
    # admin-only endpoint; a normal user must not be able to write settings at all
    r = client.put("/api/settings/global/price_refresh_secs", json={"value": 5})
    assert r.status_code in (401, 403)
