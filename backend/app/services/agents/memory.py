from typing import Optional
from typing_extensions import TypedDict
from pydantic import BaseModel, Field



class TripDetails(BaseModel):
    """Details of the trip."""
    location: str = Field(..., description="The current location of the user.")
    destination: str = Field(..., description="The destination of the trip.")
    departure_date: Optional[str] = Field(None, description="The date of departure.")
    return_date: Optional[str] = Field(None, description="The date of return.")
    budget: Optional[float] = Field(None, description="The budget for the trip.")
    adults: Optional[int] = Field(None, description="The number of adults traveling.")
    children: Optional[int] = Field(None, description="The number of children traveling.")

class UserInfo(BaseModel):
    """Information about the user."""
    username: str = Field(..., description="The username of the user.")
    email: str = Field(..., description="The email address of the user.")
    age: Optional[int] = Field(None, description="The age of the user.")
    user_description: Optional[str] = Field(None, description="A brief description of the user's personality/travel preferences.")
    location: Optional[str] = Field(None, description="The current location of the user.")

class State(TypedDict):
    """State of the agent."""
    trip_details: TripDetails
    user_info: UserInfo
