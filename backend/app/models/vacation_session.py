# ...existing code...
"""Session model to store partially-collected vacation state so a user/agent can resume."""
import uuid
from typing import Any, Dict, Optional
from datetime import datetime, timezone, timedelta

from sqlalchemy import Column, Enum, String, DateTime, ForeignKey, JSON, Boolean, Integer, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base
import enum
from app.core.config import settings

class SessionStage(str, enum.Enum):
    DISCOVERY = "discovery"
    OPTIONS = "options"
    ITINERARY = "itinerary"
    BOOKING = "booking"
    COMPLETED = "completed"

def get_expiry_date():
    """Helper to calculate the expiry date 30 days from now."""
    return datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(days=settings.SESSION_EXPIRY_DAYS)

class VacationSession(Base):
    __tablename__ = "vacation_sessions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    current_stage = Column(Enum(SessionStage), default=SessionStage.DISCOVERY, nullable=False)

    currency = Column(String, nullable=True, default="EUR")
    from_date = Column(DateTime, nullable=True)
    to_date = Column(DateTime, nullable=True)
    departure = Column(String, nullable=True)
    destination = Column(String, nullable=True)
    flights_url = Column(Text, nullable=True)
    accomodation_url = Column(Text, nullable=True)

    is_active = Column(Boolean, default=True, nullable=False)
    
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    
    updated_at = Column(DateTime, onupdate=lambda: datetime.now(timezone.utc).replace(tzinfo=None), nullable=True)
    
    expires_at = Column(
        DateTime, 
        default=get_expiry_date,
        onupdate=get_expiry_date, 
        nullable=True
    )

    user = relationship("User", back_populates="sessions", lazy="joined")
    
    def __repr__(self):
        return f"<VacationSession id={self.id} user_id={self.user_id}>"
    