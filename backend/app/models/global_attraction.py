from sqlalchemy import Column, Integer, String, Float, Text, DateTime
from sqlalchemy.sql import func
from app.core.database import Base

class GlobalAttraction(Base):
    __tablename__ = "global_attractions"

    id = Column(Integer, primary_key=True, index=True)
    
    external_place_id = Column(String, unique=True, index=True, nullable=True) # Google/OSM ID
    wikidata_id = Column(String, nullable=True)
    official_name = Column(String, index=True, nullable=False)
    
    city = Column(String, index=True, nullable=False)
    state_province = Column(String, index=True, nullable=True)
    country = Column(String, index=True, nullable=False)
    formatted_address = Column(String, nullable=True)
    timezone = Column(String, nullable=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    
    category = Column(String, index=True)
    tags = Column(String, nullable=True)
    description = Column(Text)
    image_url = Column(String, nullable=True)
    website_url = Column(String, nullable=True)
    rating = Column(Float, nullable=True)
    price_tier = Column(Integer, nullable=True)
    
    recommended_duration_mins = Column(Integer, default=120) 
    tod_preference = Column(String, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())