from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, func
from app.database import Base

class Attachment(Base):
    __tablename__ = "attachments"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # Polymorphic association
    owner_type = Column(String(50), nullable=False) # 'trade' or 'avatar'
    owner_id = Column(Integer, nullable=False)

    # File metadata
    path = Column(String(255), nullable=False)
    mime = Column(String(100))
    size = Column(Integer)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
