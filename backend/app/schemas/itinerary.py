from typing import Optional

from pydantic import BaseModel

class UpdateStageRequest(BaseModel):
    session_id: int
    stage: int

class UpdateSearchLocationRequest(BaseModel):
    session_id: int
    new_location: str

class AddToBucketRequest(BaseModel):
    session_id: int
    attraction_id: int
    name: str
    image_url: Optional[str] = None
    time_to_spend: int
    bucket: str
    location: Optional[str] = None

class SearchAttractionsRequest(BaseModel):
    session_id: int
    query: Optional[str] = None
    action: str
    
class UpdateMobilityRequest(BaseModel):
    session_id: int
    config: dict

class TransportRequest(BaseModel):
    session_id: int
    action: Optional[str] = "search_public_transport_offers"

class PaceRequest(BaseModel):
    session_id: int
    pace: str

class ScheduleActionRequest(BaseModel):
    session_id: int
    action: str

class TripDetailsRequest(BaseModel):
    session_id: int
    trip_details: Optional[dict] = None

class CustomTimelineRequest(BaseModel):
    session_id: int
    user_timeline: list[list[int]]