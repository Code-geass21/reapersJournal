import os
import uuid
import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url

_TEST_URL = os.environ.get("TEST_DATABASE_URL")
_LIVE_URL = os.environ.get("DATABASE_URL", "")

if not _TEST_URL:
    pytest.exit("TEST_DATABASE_URL is not set. Refusing to run tests.", returncode=2)

_t = make_url(_TEST_URL)
if not (_t.database or "").endswith("_test"):
    pytest.exit(f"Refusing to run: test database name must end with '_test' (got '{_t.database}').", returncode=2)
if _LIVE_URL:
    _l = make_url(_LIVE_URL)
    if (_l.host, _l.port or 5432, _l.database) == (_t.host, _t.port or 5432, _t.database):
        pytest.exit("Refusing to run: TEST_DATABASE_URL points at the live database.", returncode=2)

os.environ["DATABASE_URL"] = _TEST_URL
os.environ.setdefault("JWT_SECRET", "test-secret")
os.environ["TWELVEDATA_API_KEY"] = ""

from fastapi.testclient import TestClient  # noqa: E402
from app.main import app  # noqa: E402
from app.database import SessionLocal, engine  # noqa: E402
from app.migrate import run_migrations  # noqa: E402
from app.models.user import User  # noqa: E402
from app.models.instrument import Market, Instrument  # noqa: E402
from app.models.strategy import Strategy  # noqa: E402
from app.utils.security import get_password_hash, create_access_token  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def _fresh_migrated_database():
    admin = create_engine(_TEST_URL, isolation_level="AUTOCOMMIT")
    with admin.connect() as c:
        c.execute(text("DROP SCHEMA public CASCADE"))
        c.execute(text("CREATE SCHEMA public"))
    admin.dispose()
    run_migrations()
    yield
    engine.dispose()


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="module")
def db():
    session = SessionLocal()
    yield session
    session.close()


def _make_instrument(db, symbol, provider_symbol, pip_size, quote_ccy):
    inst = Instrument(
        market_code="FOREX",
        symbol=symbol,
        provider_symbol=provider_symbol,
        pip_size=pip_size,
        contract_size=100000,
        quote_ccy=quote_ccy
    )
    db.add(inst)
    db.flush()
    return inst


@pytest.fixture(scope="module")
def test_user_data(db):
    tag = uuid.uuid4().hex[:6].upper()
    username = f"test_{tag.lower()}"

    user = User(
        username=username,
        email=f"{username}@example.com",
        password_hash=get_password_hash("testpass"),
        role="user"
    )
    db.add(user)

    if not db.query(Market).filter(Market.code == "FOREX").first():
        db.add(Market(code="FOREX", name="Foreign Exchange"))
    db.flush()

    usd_inst = _make_instrument(db, f"T{tag}USD", f"T{tag}USD=X", 0.0001, "USD")
    jpy_inst = _make_instrument(db, f"T{tag}JPY", f"T{tag}JPY=X", 0.01, "JPY")

    strat = Strategy(
        user_id=user.id,
        name="Test Strategy Integration",
        market="FOREX"
    )
    db.add(strat)
    db.commit()

    ids = (user.id, usd_inst.id, jpy_inst.id)
    token = create_access_token({"sub": user.username, "role": user.role})

    yield {
        "user_id": user.id,
        "token": token,
        "headers": {"Authorization": f"Bearer {token}"},
        "instrument_id": usd_inst.id,
        "jpy_instrument_id": jpy_inst.id,
        "jpy_conversion_symbol": f"USD{jpy_inst.quote_ccy}=X",
        "strategy_id": strat.id,
    }

    db.rollback()
    db.expunge_all()
    db.execute(text("DELETE FROM users WHERE id = :u"), {"u": ids[0]})
    db.execute(text("DELETE FROM instruments WHERE id IN (:a, :b)"), {"a": ids[1], "b": ids[2]})
    db.commit()
