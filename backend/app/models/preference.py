from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import relationship
from app.database import Base

class UserPreference(Base):
    __tablename__ = "user_preferences"

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    theme = Column(String(20), default="dark")
    default_strategy_ids = Column(ARRAY(Integer), server_default='{}')
    default_market = Column(String(50), default="FOREX")
    refresh_secs = Column(Integer, default=30)

    # Links back to the User model
    user = relationship("User", back_populates="preferences")
