from typing import Optional

from pydantic import BaseModel

class AddToBucketRequest(BaseModel):
    session_id: int
    attraction_id: int
    time_to_spend: int
    bucket: str

class SearchAttractionsRequest(BaseModel):
    session_id: int
    query: Optional[str] = None
    action: str
    
