import pytest
import uuid
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from app.main import app
from app.database import get_db, Base
from app.models.user import User
from app.models.instrument import Market, Instrument
from app.models.strategy import Strategy
from app.utils.security import get_password_hash, create_access_token

# FIX FOR BUG 90: Isolate tests using a local SQLite database
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///./test_reapers.db"
engine = create_engine(SQLALCHEMY_TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create all tables in the test database on startup
Base.metadata.create_all(bind=engine)

# Override FastAPI's database dependency for the TestClient
def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c

@pytest.fixture(scope="module")
def db():
    session = TestingSessionLocal()
    yield session
    session.close()

@pytest.fixture(scope="module")
def test_user_data(db: Session):
    """
    Creates a temporary user, strategy, and instrument for testing.
    Automatically wipes them all from the database when tests finish.
    """
    username = f"test_{uuid.uuid4().hex[:8]}"

    # 1. Create User
    user = User(
        username=username,
        email=f"{username}@example.com",
        password_hash=get_password_hash("testpass"),
        role="user"
    )
    db.add(user)

    # 2. Ensure FOREX market exists
    market = db.query(Market).filter(Market.code == "FOREX").first()
    if not market:
        market = Market(code="FOREX", name="Foreign Exchange")
        db.add(market)

    db.flush()

    # 3. Create a dummy instrument
    inst = Instrument(
        market_code="FOREX",
        symbol=f"TST{username[:4]}",
        provider_symbol=f"TST{username[:4]}=X",
        pip_size=0.0001,
        contract_size=100000,
        quote_ccy="USD"
    )
    db.add(inst)

    # 4. Create a dummy strategy
    strat = Strategy(
        user_id=user.id,
        name="Test Strategy Integration",
        market="FOREX"
    )
    db.add(strat)
    db.commit()

    # 5. Generate Auth Token
    token = create_access_token({"sub": user.username, "role": user.role})

    yield {
        "user_id": user.id,
        "token": token,
        "headers": {"Authorization": f"Bearer {token}"},
        "instrument_id": inst.id,
        "strategy_id": strat.id
    }

    # TEARDOWN: ON DELETE CASCADE will safely wipe all test trades and executions!
    db.delete(user)
    db.delete(inst)
    db.commit()
