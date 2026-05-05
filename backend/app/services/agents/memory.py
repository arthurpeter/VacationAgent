from typing import Optional, Annotated, List, Union
from typing_extensions import TypedDict
from pydantic import BaseModel, Field
from langgraph.graph.message import add_messages


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
    
    persona_context: Optional[str] = None
    data: Optional[dict] = None
    action: Optional[str] = None
    pois: Optional[List[dict]] = None
    daily_themes: Optional[dict[int, str]] = None
    daily_plans: Optional[dict[int, str]] = None
    daily_links: Optional[dict[int, List[dict[str, str]]]] = None
    recently_detailed_days: Optional[List[int]] = None
    are_themes_confirmed: bool = False
    transit_strategy: Optional[dict] = None
