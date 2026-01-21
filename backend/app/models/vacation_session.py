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

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    data = Column(JSON, nullable=True, default={})
    currency = Column(String, nullable=True, default="EUR")
    current_step = Column(String, nullable=True)
    last_question = Column(Text, nullable=True)
    messages = Column(JSON, nullable=True)
    agent_state = Column(JSON, nullable=True)

    is_active = Column(Boolean, default=True, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    expires_at = Column(DateTime(timezone=True), onupdate=func.now() + timedelta(days=settings.SESSION_EXPIRY_DAYS), nullable=True)

    user = relationship("User", back_populates="sessions", lazy="joined")

    def to_final_payload(self) -> Dict[str, Any]:
        return dict(self.data or {})

    def patch(self, patch_dict: Dict[str, Any]) -> None:
        d = dict(self.data or {})
        d.update(patch_dict)
        self.data = d
        self.version = (self.version or 1) + 1
    
    def __repr__(self):
        return f"<VacationSession id={self.id} user_id={self.user_id} current_step={self.current_step!r}>"