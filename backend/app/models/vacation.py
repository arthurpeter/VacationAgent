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
    from_date = Column(String, nullable=True)
    to_date = Column(String, nullable=True)
    people_count = Column(Integer, nullable=True)
    
    flight_price = Column(Float, nullable=True)
    flight_ccy = Column(String, nullable=True)    
    accomodation_price = Column(Float, nullable=True)
    accomodation_ccy = Column(String, nullable=True)
    itinerary_data = Column(JSON, nullable=True)
    transit_strategy = Column(JSON, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    user = relationship("User", back_populates="vacations", lazy="selectin")

    def __repr__(self):
        return f"<Vacation id={self.id} destination={self.destination!r} user_id={self.user_id}>"