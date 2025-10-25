"""User model for AuthX authentication."""
import uuid
from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, Text, JSON, Numeric
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class Vacation(Base):
    __tablename__ = "vacations"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    
    # basic trip info
    departure = Column(String, nullable=False)
    destination = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    
    # core dates
    start_date = Column(DateTime(timezone=True), nullable=False)
    end_date = Column(DateTime(timezone=True), nullable=False)

    # detailed components for the vacation
    flights = Column(JSON, nullable=True)
    hotels = Column(JSON, nullable=True)
    itinerary = Column(Text, nullable=True)

    total_price = Column(Numeric(12, 2), nullable=True)
    currency = Column(String(8), nullable=True)

    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

    user = relationship("User", back_populates="vacations", lazy="selectin")

    def __repr__(self):
        return f"<Vacation id={self.id} destination={self.destination!r} user_id={self.user_id}>"