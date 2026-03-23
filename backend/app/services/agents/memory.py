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
    vibe: Optional[str] = None
    description: Optional[str] = None
    is_complete: bool = False
    passengers_confirmed: bool = False
