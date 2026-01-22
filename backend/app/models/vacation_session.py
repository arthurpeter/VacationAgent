# ...existing code...
"""Session model to store partially-collected vacation state so a user/agent can resume."""
import uuid
from typing import Any, Dict, Optional
from datetime import datetime, timezone, timedelta

from sqlalchemy import Column, String, DateTime, ForeignKey, JSON, Boolean, Integer, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base

from app.core.config import settings


class VacationSession(Base):
    __tablename__ = "vacation_sessions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    currency = Column(String, nullable=True, default="EUR")
    from_date = Column(DateTime(timezone=True), nullable=True)
    to_date = Column(DateTime(timezone=True), nullable=True)
    destination = Column(String, nullable=True)
    flights_url = Column(Text, nullable=True)
    accomodation_url = Column(Text, nullable=True)

    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    expires_at = Column(DateTime(timezone=True), onupdate=func.now() + timedelta(days=settings.SESSION_EXPIRY_DAYS), nullable=True)

    user = relationship("User", back_populates="sessions", lazy="joined")
    
    def __repr__(self):
        return f"<VacationSession id={self.id} user_id={self.user_id} current_step={self.current_step!r}>"