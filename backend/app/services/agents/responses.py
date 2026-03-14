from pydantic import BaseModel, Field
from typing import Optional, List

class ExtractionResult(BaseModel):
    """Reflects all mandatory and optional slots in VacationSession."""
    
    departure: Optional[str] = Field(None, description="'City, country_code' for departure")
    destination: Optional[str] = Field(None, description="'City, country_code' for arrival")
    from_date: Optional[str] = Field(None, description="Departure date in YYYY-MM-DD format")
    to_date: Optional[str] = Field(None, description="Return date in YYYY-MM-DD format")
    currency: Optional[str] = Field(None, description="ISO currency code, e.g., 'USD', 'EUR'")
    
    adults: Optional[int] = Field(None, description="Number of adults (12+ years old)")
    children: Optional[int] = Field(None, description="Number of children (2-11 years old)")
    infants_in_seat: Optional[int] = Field(None, description="Number of infants (0-2 years old) with their own seat")
    infants_on_lap: Optional[int] = Field(None, description="Number of infants (0-2 years old) sitting on an adult's lap")
    children_ages: Optional[str] = Field(
        None, 
        description="Comma-separated ages of children, e.g., '5,12'. Must match child+infant count."
    )
    
    room_qty: Optional[int] = Field(None, description="Number of hotel rooms needed")
    
    is_change_request: bool = Field(
        False,
        description="True if the user is explicitly correcting or changing existing info"
    )