"""Global attractions cache for initial itinerary POIs."""
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Float, Integer, String, Text
from sqlalchemy.sql import func

from app.core.database import Base


class GlobalAttraction(Base):
    __tablename__ = "global_attractions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    external_place_id = Column(String, unique=True, nullable=False, index=True)
    city_name = Column(String, nullable=False, index=True)
    name = Column(String, nullable=False)
    category = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    image_url = Column(Text, nullable=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    duration_mins = Column(Integer, nullable=True, default=90)

    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime,
        onupdate=lambda: datetime.now(timezone.utc).replace(tzinfo=None),
        nullable=True
    )

    def __repr__(self):
        return f"<GlobalAttraction id={self.id} name={self.name} city={self.city_name}>"
