"""User model for AuthX authentication."""
import uuid
from sqlalchemy import Column, String, DateTime, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class User(Base):
    """User model for AuthX authentication."""
    __tablename__ = "users"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    date_of_birth = Column(DateTime(timezone=True), nullable=True)
    location = Column(String, nullable=True)
    user_description = Column(String, nullable=True)

    # finalized vacations
    vacations = relationship(
        "Vacation",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    # active/in-progress sessions for resuming AI-driven interactions
    sessions = relationship(
        "VacationSession",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
