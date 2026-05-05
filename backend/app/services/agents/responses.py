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

class DailyTheme(BaseModel):
    day_number: int = Field(description="The day number of the trip (e.g., 1, 2, 3)")
    theme: str = Field(description="A high-level title/theme for the day. e.g., 'Arrival & Trastevere Food Tour'")

class ArchitectResult(BaseModel):
    themes: List[DailyTheme] = Field(description="The complete list of high-level themes for EVERY day of the trip.")

class DetailerResult(BaseModel):
    """CRITICAL: Use this tool to submit the detailed daily plans you create for each day of the itinerary."""
    day_number: int = Field(description="The specific day being detailed")
    detailed_plan: str = Field(description="The full schedule (Morning, Afternoon, Evening) formatted in Markdown")

class ResourceLink(BaseModel):
    name: str = Field(description="Name of the place, activity, or restaurant")
    url: str = Field(description="A valid URL to book or learn more")

class SubmitLinks(BaseModel):
    """CRITICAL: Use this tool to submit the final list of official links you found for the day's activities."""
    day_number: int = Field(description="The specific day these links belong to")
    links: List[ResourceLink] = Field(description="The list of links found")

class SaveTransitStrategy(BaseModel):
    """Saves the final recommended transit pass strategy to the database/state."""
    pass_name: str = Field(description="The exact name of the recommended pass (e.g., 'Navigo Easy', 'Oyster Card').")
    description: str = Field(description="A brief explanation of why this is the best option and what it covers.")
    price: str = Field(description="The estimated cost (e.g., '€29.90', '£15.00').")
    purchase_url: str = Field(description="The official website URL where the user can buy or read more about this exact pass.")
