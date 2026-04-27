import orjson

from langgraph.graph import START, END, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langchain_core.messages import HumanMessage
from psycopg_pool import AsyncConnectionPool
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.agents.memory import ItineraryState
from app.services.agents.nodes import global_architect, focused_detailer, link_finder, itinerary_responder, save_links_and_cleanup, save_details_and_cleanup
from app.services.agents.utils import get_initial_itinerary_state
from app.services.agents.tools import link_finder_tools, detailer_tools
from app.core.logger import get_logger

log = get_logger(__name__)

def route_phase(state: ItineraryState):
    """
    The Gatekeeper: Routes the graph based on the user's UI action.
    """
    if state.get("are_themes_confirmed"):
        return "focused_detailer"
    return "global_architect"

def route_link_finder(state: ItineraryState):
    """The Traffic Cop for the ReAct loop."""
    messages = state.get("messages", [])
    if not messages:
        return "itinerary_responder"
    
    last_message = messages[-1]
    
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        if any(tc["name"] == "SubmitLinks" for tc in last_message.tool_calls):
            return "save_links_and_cleanup"
        
        return "link_finder_tools"
        
    return "itinerary_responder"

def route_detailer(state: ItineraryState):
    """Decides whether to call detailer tools or not."""
    messages = state.get("messages", [])
    if not messages:
        return "itinerary_responder"
    
    last_message = messages[-1]
    
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        if any(tc["name"] == "DetailerResult" in [tool.name for tool in detailer_tools] for tc in last_message.tool_calls):
            return "save_details_and_cleanup"
        return "detailer_tools"
        
    return "link_finder"

def generate_graph(checkpointer=None):
    
    builder = StateGraph(ItineraryState)
    builder.add_node("global_architect", global_architect)
    builder.add_node("focused_detailer", focused_detailer)
    builder.add_node("link_finder", link_finder)
    builder.add_node("itinerary_responder", itinerary_responder)
    builder.add_node("link_finder_tools", ToolNode(link_finder_tools))
    builder.add_node("detailer_tools", ToolNode(detailer_tools))
    builder.add_node("save_links_and_cleanup", save_links_and_cleanup)
    builder.add_node("save_details_and_cleanup", save_details_and_cleanup)

    builder.add_conditional_edges(START, route_phase, {
            "focused_detailer": "focused_detailer",
            "global_architect": "global_architect"
        })
    builder.add_edge("global_architect", "itinerary_responder")
    builder.add_edge("focused_detailer", "link_finder")
    builder.add_conditional_edges("link_finder", route_link_finder, {
            "save_links_and_cleanup": "save_links_and_cleanup",
            "link_finder_tools": "link_finder_tools",
            "itinerary_responder": "itinerary_responder"
        })
    builder.add_conditional_edges("focused_detailer", route_detailer, {
            "detailer_tools": "detailer_tools",
            "save_details_and_cleanup": "save_details_and_cleanup",
            "itinerary_responder": "itinerary_responder"
        })
    builder.add_edge("link_finder_tools", "link_finder")
    builder.add_edge("detailer_tools", "focused_detailer")
    builder.add_edge("save_links_and_cleanup", "itinerary_responder")
    builder.add_edge("itinerary_responder", END)

    return builder.compile(checkpointer=checkpointer)

async def stream_itinerary_message(
    session_id: int, 
    user_message: str, 
    db: AsyncSession, 
    checkpointer: AsyncPostgresSaver
):
    graph = generate_graph(checkpointer) 
    config = {"configurable": {"thread_id": f"itinerary_{session_id}"}}

    current_state = await graph.aget_state(config)

    if not current_state.values:
        log.info(f"Starting new LangGraph itinerary thread for session {session_id}...")
        input_data = await get_initial_itinerary_state(db, session_id)
        input_data["messages"].append(HumanMessage(content=user_message))
    else:
        log.info(f"Resuming existing LangGraph itinerary thread for session {session_id}...")
        input_data = {
            "messages": [HumanMessage(content=user_message)]
        }

    final_ai_text = ""

    async for event in graph.astream(input_data, config=config, stream_mode="updates"):
        for node_name, node_updates in event.items():
            
            new_messages = node_updates.get("messages", [])
            if new_messages:
                last_msg = new_messages[-1] if isinstance(new_messages, list) else new_messages
                if getattr(last_msg, "type", "") == "ai":
                    final_ai_text = last_msg.content
            
            payload = {
                "status": "processing",
                "current_node": node_name,
                "daily_themes": node_updates.get("daily_themes"),
                "daily_plans": node_updates.get("daily_plans"),
                "daily_links": node_updates.get("daily_links"),
            }
            
            yield f"data: {orjson.dumps(payload, option=orjson.OPT_NON_STR_KEYS).decode()}\n\n"

    final_payload = {
        "status": "complete", 
        "ai_message": final_ai_text
    }
    yield f"data: {orjson.dumps(final_payload).decode()}\n\n"


if __name__ == "__main__":
    print("This module is not meant to be run directly. It provides the execution graph for the itinerary process.\n\n")
    my_graph = generate_graph()
    
    png_bytes = my_graph.get_graph(xray=True).draw_mermaid_png()
    
    with open("itinerary_graph_v1.png", "wb") as f:
        f.write(png_bytes)
        
    print("Graph saved successfully to itinerary_graph_v1.png!")