from sqlalchemy import Column, String, Numeric, DateTime
from sqlalchemy.sql import func
from app.database import Base

class PriceCache(Base):
    __tablename__ = "price_cache"

    provider_symbol = Column(String(50), primary_key=True, index=True)
    price = Column(Numeric(20, 10))
    bid = Column(Numeric(20, 10))
    ask = Column(Numeric(20, 10))
    fetched_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    # FIX FOR BUG 37: Changed default from yfinance to twelvedata
    source = Column(String(50), default="twelvedata")
