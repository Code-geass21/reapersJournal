from sqlalchemy import Column, Integer, String, Boolean, DateTime, Numeric, Text, ForeignKey, func
from sqlalchemy.dialects.postgresql import JSONB, ARRAY
from sqlalchemy.orm import relationship
from app.database import Base

class Trade(Base):
    __tablename__ = "trades"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    strategy_id = Column(Integer, ForeignKey("strategies.id", ondelete="CASCADE"), nullable=False)
    instrument_id = Column(Integer, ForeignKey("instruments.id", ondelete="RESTRICT"), nullable=False)

    direction = Column(String(10), nullable=False)
    status = Column(String(20), default='open')
    entry_price = Column(Numeric(15, 5), nullable=False)
    size = Column(Numeric(15, 2), nullable=False)
    stop_loss = Column(Numeric(15, 5))
    take_profit = Column(Numeric(15, 5))

    opened_at = Column(DateTime(timezone=True), server_default=func.now())
    closed_at = Column(DateTime(timezone=True))
    exit_price = Column(Numeric(15, 5))
    fees = Column(Numeric(15, 2), default=0)
    pnl_realized = Column(Numeric(15, 2))
    r_multiple = Column(Numeric(10, 2))

    notes = Column(Text)
    tags = Column(ARRAY(Text), default=[])
    emotion = Column(String(50))
    rule_violations = Column(JSONB, server_default='{}')

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    instrument = relationship("Instrument", back_populates="trades")
    # Link back to strategy (you will need to add `trades = relationship("Trade", back_populates="strategy")` to Strategy model later)
    condition_checks = relationship("TradeConditionCheck", back_populates="trade", cascade="all, delete-orphan")

class TradeConditionCheck(Base):
    __tablename__ = "trade_condition_checks"

    id = Column(Integer, primary_key=True, index=True)
    trade_id = Column(Integer, ForeignKey("trades.id", ondelete="CASCADE"), nullable=False)
    rule_id = Column(Integer, ForeignKey("strategy_rules.id", ondelete="CASCADE"), nullable=False)
    passed = Column(Boolean, nullable=False)
    note = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    trade = relationship("Trade", back_populates="condition_checks")
