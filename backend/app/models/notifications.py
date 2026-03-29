from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, Text, Integer
from sqlalchemy.sql import func
from app.core.database import Base

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    category = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    event_key = Column(String, unique=True, nullable=True) 
    is_read = Column(Boolean, default=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True) 
    created_at = Column(DateTime(timezone=True), server_default=func.now())