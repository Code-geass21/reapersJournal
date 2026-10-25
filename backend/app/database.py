import time
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.exc import OperationalError
from app.config import settings

# --- Retry Logic Added Here ---
MAX_RETRIES = 5
RETRY_DELAY_SECS = 2

engine = None
for i in range(MAX_RETRIES):
    try:
        print(f"Attempting to connect to database (Attempt {i + 1}/{MAX_RETRIES})...")
        engine = create_engine(settings.database_url)
        # Try to connect to verify it's ready
        with engine.connect() as conn:
            print("Successfully connected to the database!")
        break
    except OperationalError as e:
        if i == MAX_RETRIES - 1:
            print("Failed to connect to database after maximum retries.")
            raise e
        print(f"Database not ready yet. Waiting {RETRY_DELAY_SECS} seconds...")
        time.sleep(RETRY_DELAY_SECS)
# ------------------------------

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
