from sqlalchemy import Column, Integer, String, DateTime, func
from app.database import Base

class NewsEvent(Base):
    __tablename__ = "news_events"

    id = Column(Integer, primary_key=True, index=True)
    event_time_utc = Column(DateTime(timezone=True), nullable=False)
    currency = Column(String(10), nullable=False)
    impact = Column(String(20))
    title = Column(String(255), nullable=False)
    forecast = Column(String(50))
    previous = Column(String(50))
    actual = Column(String(50))
    source_uid = Column(String(100), unique=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
