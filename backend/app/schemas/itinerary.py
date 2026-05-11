from typing import Optional

from pydantic import BaseModel

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

class SearchAttractionsRequest(BaseModel):
    session_id: int
    query: Optional[str] = None
    action: str
    
