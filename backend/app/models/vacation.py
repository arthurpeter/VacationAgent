"""User model for AuthX authentication."""
import uuid
from sqlalchemy import Column, Float, Integer, String, DateTime, Boolean, ForeignKey, Text, JSON, Numeric
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class Vacation(Base):
    __tablename__ = "vacations"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    session_id = Column(Integer, unique=True, nullable=True)

    destination = Column(String, nullable=False)
    origin = Column(String, nullable=True)
    from_date = Column(DateTime(timezone=False), nullable=True)
    to_date = Column(DateTime(timezone=False), nullable=True)
    adults = Column(Integer, default=1, nullable=False)
    children = Column(Integer, default=0, nullable=False)
    
    flights_url = Column(Text, nullable=True)
    flight_price = Column(Float, nullable=True)
    flight_ccy = Column(String, nullable=True)
    airport_name = Column(String, nullable=True)
    accommodation_url = Column(Text, nullable=True)
    accommodation_price = Column(Float, nullable=True)
    accommodation_ccy = Column(String, nullable=True)
    accommodation_name = Column(String, nullable=True)
    accommodation_address = Column(String, nullable=True)

    itinerary_data = Column(JSON, nullable=True)
    
    is_finalized = Column(Boolean, default=False, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    user = relationship("User", back_populates="vacations", lazy="selectin")

    def __repr__(self):
        return f"<Vacation id={self.id} destination={self.destination!r} user_id={self.user_id}>"