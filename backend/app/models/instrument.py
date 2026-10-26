from sqlalchemy import Column, Integer, String, Boolean, Numeric, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class Market(Base):
    __tablename__ = "markets"

    code = Column(String(20), primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    is_enabled = Column(Boolean, default=True)

    instruments = relationship("Instrument", back_populates="market", cascade="all, delete-orphan")

class Instrument(Base):
    __tablename__ = "instruments"

    id = Column(Integer, primary_key=True, index=True)
    market_code = Column(String(20), ForeignKey("markets.code", ondelete="CASCADE"), nullable=False)
    symbol = Column(String(50), nullable=False)
    provider_symbol = Column(String(50), nullable=False)
    pip_size = Column(Numeric(10, 5), nullable=False)
    contract_size = Column(Integer, default=100000)
    quote_ccy = Column(String(10), nullable=False)
    is_active = Column(Boolean, default=True)

    market = relationship("Market", back_populates="instruments")
    trades = relationship("Trade", back_populates="instrument")
