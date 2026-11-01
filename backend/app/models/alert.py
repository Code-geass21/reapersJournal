from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, func
from app.database import Base

class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    trade_id = Column(Integer, ForeignKey("trades.id", ondelete="CASCADE"), nullable=True)
    kind = Column(String(50), nullable=False)
    message = Column(Text, nullable=False)
    status = Column(String(20), default="new")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
