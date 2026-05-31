import operator
from typing import Any, Optional, Annotated, List, Union
from typing_extensions import Literal, TypedDict
from pydantic import BaseModel, Field
from langgraph.graph.message import add_messages

from app.services.agents.responses import MobilityRecommendationSchema, PaceRecommendationSchema


class DiscoveryState(TypedDict):
    messages: Annotated[List[Union[dict, str]], add_messages]
    user_id: str
    session_id: int
    
    persona_context: Optional[str] = None
    newly_extracted_data: Optional[dict] = None
    extracted_data: Optional[dict] = None
    tool_outputs: List[str] = []
    #vibe: Optional[str] = None
    description: Optional[str] = None
    user_history: Optional[str] = None
    is_complete: bool = False
    passengers_confirmed: bool = False

class ItineraryState(TypedDict):
    messages: Annotated[List[Union[dict, str]], add_messages]
    user_id: str
    session_id: int
    stage: int = 0
    action: Optional[str] = None
    search_location: Optional[str] = None
    
    persona_context: Optional[str] = None
    data: Optional[dict] = None
    pois: List[dict[str, Any]] = []
    unresolved_attractions: List[dict[str, Any]] = []
    resolved_attractions: Annotated[List[dict[str, Any]], operator.add] = []

    mobility_config: Optional[dict] = None
    mobility_recommendation: Optional[MobilityRecommendationSchema] = None
    pace_recommendation: Optional[PaceRecommendationSchema] = None
    pace: Literal["Relaxed", "Moderate", "Fast-Paced"] = "Moderate"

    trip_details: Optional[dict[str, Any]] = None
    schedule: Optional[List[dict[str, Any]]] = None
    excluded_pois: Optional[dict[str, List[str]]] = None
    

    user_timeline: Optional[List[List[int]]] = None

