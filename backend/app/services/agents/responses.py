from typing import Optional
from pydantic import BaseModel, Field


class InformationCollectorResponse(BaseModel):
    user_description: Optional[str] = Field(None, description="A brief description of the user's personality.")
    description: Optional[str] = Field(None, description="A description of what the user wants (the scope of the trip, types of activities, etc.).")
    departure_date: Optional[str] = Field(None, description="The date of departure YYYY-MM-DD format.")
    return_date: Optional[str] = Field(None, description="The date of return YYYY-MM-DD format.")
    budget: Optional[float] = Field(None, description="The budget for the trip.")
    adults: Optional[int] = Field(None, description="The number of adults traveling.")
    children: Optional[int] = Field(None, description="The number of children traveling.")
    follow_up_question: Optional[str] = Field(None, description="Follow-up question to get information from the user.")