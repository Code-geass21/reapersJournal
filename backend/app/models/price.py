from sqlalchemy import Column, String, Numeric, DateTime, func
from app.database import Base

class PriceCache(Base):
    __tablename__ = "price_cache"

    provider_symbol = Column(String(50), primary_key=True, index=True)
    price = Column(Numeric(15, 5), nullable=False)
    bid = Column(Numeric(15, 5))
    ask = Column(Numeric(15, 5))
    fetched_at = Column(DateTime(timezone=True), server_default=func.now())
    source = Column(String(50), default="yfinance")
