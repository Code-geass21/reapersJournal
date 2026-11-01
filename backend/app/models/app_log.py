from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import JSONB
from app.database import Base

class AppLog(Base):
    __tablename__ = "app_logs"

    id = Column(Integer, primary_key=True, index=True)
    ts = Column(DateTime(timezone=True), server_default=func.now())
    level = Column(String(20), default="INFO")
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    action = Column(String(100), nullable=False)
    entity_type = Column(String(50))
    entity_id = Column(Integer)
    before = Column(JSONB)
    after = Column(JSONB)
    source = Column(String(50), default="api")
    error_text = Column(Text)
    request_id = Column(String(100))
