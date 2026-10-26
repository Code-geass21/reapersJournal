from sqlalchemy import Column, Integer, String, Boolean, DateTime, Date, Numeric, Text, ForeignKey, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from app.database import Base

class Strategy(Base):
    __tablename__ = "strategies"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    market = Column(String(50), default="FOREX")
    funding_mode = Column(String(50), default="non_systematic")
    sip_amount = Column(Numeric(15, 2))
    sip_frequency = Column(String(50))
    start_date = Column(Date)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    rules = relationship("StrategyRule", back_populates="strategy", cascade="all, delete-orphan")
    deposits = relationship("StrategyDeposit", back_populates="strategy", cascade="all, delete-orphan")
    trades = relationship("Trade", back_populates="strategy")

class StrategyRule(Base):
    __tablename__ = "strategy_rules"

    id = Column(Integer, primary_key=True, index=True)
    strategy_id = Column(Integer, ForeignKey("strategies.id", ondelete="CASCADE"), nullable=False)
    rule_type = Column(String(50), nullable=False)
    label = Column(String(255), nullable=False)
    params = Column(JSONB, server_default='{}')
    is_required = Column(Boolean, default=True)
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    strategy = relationship("Strategy", back_populates="rules")

class StrategyDeposit(Base):
    __tablename__ = "strategy_deposits"

    id = Column(Integer, primary_key=True, index=True)
    strategy_id = Column(Integer, ForeignKey("strategies.id", ondelete="CASCADE"), nullable=False)
    amount = Column(Numeric(15, 2), nullable=False)
    kind = Column(String(20), nullable=False)
    date = Column(Date, nullable=False)
    note = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    strategy = relationship("Strategy", back_populates="deposits")
