from pydantic import BaseModel, Field
from typing import Optional, List

class ExtractionResult(BaseModel):
    """Reflects all mandatory and optional slots in VacationSession."""
    
    departure: Optional[str] = Field(None, description="'City, country_code' for departure, e.g., 'New York, US'")
    destination: Optional[str] = Field(None, description="'City, country_code' for arrival, e.g., 'Paris, FR'")
    from_date: Optional[str] = Field(None, description="Departure date in YYYY-MM-DD format")
    to_date: Optional[str] = Field(None, description="Return date in YYYY-MM-DD format")
    currency: Optional[str] = Field(None, description="ISO currency code, e.g., 'USD', 'EUR'")
    budget: Optional[int] = Field(None, description="The maximum total budget the user wants to spend for the trip, as an integer (e.g., 5000)")
    
    adults: Optional[int] = Field(None, description="Number of adults (12+ years old)")
    children: Optional[int] = Field(None, description="Number of children (2-11 years old)")
    infants_in_seat: Optional[int] = Field(None, description="Number of infants (0-2 years old) with their own seat")
    infants_on_lap: Optional[int] = Field(None, description="Number of infants (0-2 years old) sitting on an adult's lap")
    children_ages: Optional[str] = Field(
        None, 
        description="Comma-separated ages of children, e.g., '5,12'. Must match child+infant count."
    )
    
    room_qty: Optional[int] = Field(None, description="Number of hotel rooms needed")

    passengers_confirmed: Optional[bool] = Field(
        default=None, 
        description="Set to True if the user confirms with the assistant that the passanger counts are correct, even if they haven't explicitly mentioned them in the chat. This helps us avoid relying on system defaults without user confirmation."
    )
    
    is_change_request: bool = Field(
        False,
        description="True if the user is explicitly correcting or changing existing info"
    )