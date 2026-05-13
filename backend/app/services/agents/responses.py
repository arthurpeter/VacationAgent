from pydantic import BaseModel, Field
from typing import Dict, Optional, List

class ExtractionResult(BaseModel):
    """Reflects all mandatory and optional slots in VacationSession."""
    
    departure: Optional[str] = Field(None, description="'City, country_code' for departure, e.g., 'New York, US'")
    destination: Optional[str] = Field(None, description="'City, country_code' for arrival, e.g., 'Paris, FR'")
    from_date: Optional[str] = Field(None, description="Departure date in YYYY-MM-DD format")
    to_date: Optional[str] = Field(None, description="Return date in YYYY-MM-DD format")
    currency: Optional[str] = Field(None, description="ISO currency code, e.g., 'USD', 'EUR'")
    budget: Optional[int] = Field(None, description="The maximum total budget the user wants to spend for the trip, as an integer (e.g., 5000)")
    
    adults: Optional[int] = Field(None, description="Number of adults (18+ years old)")
    children: Optional[int] = Field(None, description="Number of children (2-17 years old)")
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

class AttractionList(BaseModel):
    attractions: List[str] = Field(
        description="A list of up to 15 specific, highly famous tourist attractions, museums, or landmarks."
    )

class OperatingHours(BaseModel):
    monday: Optional[str] = Field(description="e.g., 09:00-18:00 or Closed")
    tuesday: Optional[str] = Field(description="e.g., 09:00-18:00 or Closed")
    wednesday: Optional[str] = Field(description="e.g., 09:00-18:00 or Closed")
    thursday: Optional[str] = Field(description="e.g., 09:00-18:00 or Closed")
    friday: Optional[str] = Field(description="e.g., 09:00-18:00 or Closed")
    saturday: Optional[str] = Field(description="e.g., 09:00-18:00 or Closed")
    sunday: Optional[str] = Field(description="e.g., 09:00-18:00 or Closed")

class AttractionEnrichmentSchema(BaseModel):
    city: str = Field(
        description="The standard English name of the city this attraction is in (e.g., 'Rome' instead of 'Roma', 'Munich' instead of 'München')."
    )
    country: str = Field(
        description="The standard 2-letter Country Code (e.g., 'IT' instead of 'Italy', 'DE' instead of 'Germany')."
    )
    price_tier: Optional[int] = Field(
        description="A number from 1 to 5 representing the cost (1=Free, 2=Cheap, 3=Moderate, 4=Expensive, 5=Very Expensive)."
    )
    recommended_duration_mins: int = Field(
        default=120, 
        description="Recommended time to spend at the attraction in minutes (e.g., 60, 120, 180)."
    )
    tod_preference: Optional[str] = Field(
        description="Best time of day to visit (e.g., 'Morning', 'Afternoon', 'Evening', or 'Any')."
    )
    rating: Optional[float] = Field(
        description="The standard user rating out of 5 stars (e.g., 4.5, 4.8). Look for Google Maps or TripAdvisor ratings in the text."
    )
    website_url: Optional[str] = Field(
        description="The official website URL for tickets or visitor information."
    )
    description: str = Field(
        description="Write a short, engaging 2-3 sentence travel description based on the search context."
    )
    opening_hours: OperatingHours = Field(
        description="The weekly opening hours for the attraction. Use the format 'HH:MM-HH:MM' for each day, or 'Closed' if not open that day."
    )

class TransitEnrichmentSchema(BaseModel):
    official_link: str = Field(description="The URL to the official city public transport website or tourist pass page.")
    pass_price_est: float = Field(description="The estimated cost for a standard 48h or 72h tourist transport pass. Numeric value only.")
    currency: str = Field(description="The 3-letter ISO currency code for the price (e.g., EUR, RON, USD).")
    operating_hours: Dict[str, str] = Field(
        description="General daily operating window. Keys: 'open' and 'close'. Format: HH:MM",
        default={"open": "05:30", "close": "23:30"}
    )
    details_found: bool = Field(description="Set to true if specific 2026 price data was found, false if estimated.")

class RentalEnrichmentSchema(BaseModel):
    official_link: str = Field(description="URL to a major rental aggregator or local provider in the city.")
    daily_price_est: float = Field(description="Estimated daily cost for an economy car hire.")
    currency: str = Field(description="ISO currency code (e.g., EUR).")
    ztl_warning: bool = Field(description="True if the city has strict Limited Traffic Zones (ZTL) or high congestion fees.")
    operating_hours: Dict[str, str] = Field(
        description="Standard rental office hours. Keys: 'open', 'close'. Format: HH:MM",
        default={"open": "08:00", "close": "20:00"}
    )
