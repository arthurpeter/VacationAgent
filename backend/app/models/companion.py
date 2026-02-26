import uuid
from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base

class TravelCompanion(Base):
    """Model for a user's usual travel companions (Traveler Vault)."""
    __tablename__ = "travel_companions"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    name = Column(String, nullable=False)
    date_of_birth = Column(DateTime(timezone=True), nullable=False)
    description = Column(String, nullable=True)
    is_infant_on_lap = Column(Boolean, default=False)

    user = relationship("User", back_populates="companions")