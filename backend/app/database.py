from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.config import settings

engine = create_engine(settings.database_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Import all models here to ensure they are registered with SQLAlchemy's metadata
# BEFORE any queries are made. This resolves "failed to locate a name" circular dependency errors.
from app.models import user, strategy, instrument, trade
