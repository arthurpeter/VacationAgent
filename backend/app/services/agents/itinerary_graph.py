import orjson

from langgraph.graph import START, END, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langchain_core.messages import HumanMessage
from psycopg_pool import AsyncConnectionPool
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.agents.memory import ItineraryState
from app.services.agents.nodes import *
from app.services.agents.utils import get_initial_itinerary_state
from app.services.agents.tools import link_finder_tools, detailer_tools
from app.core.logger import get_logger

log = get_logger(__name__)

def route_stage(state: ItineraryState):
    if state.stage == 0:
        return "picking_attractions"
    elif state.stage == 1:
        return "picking_transit"
    elif state.stage == 2:
        return "organizing_days"
    elif state.stage == 3:
        return "organizing_attractions"
    else:
        return "picking_attractions"

def generate_graph(checkpointer=None):
    
    builder = StateGraph(ItineraryState)
    

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

            if not node_updates or not isinstance(node_updates, dict):
                continue
            
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
                "transit_strategy": node_updates.get("transit_strategy"),
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
    
    with open("itinerary_graph_v2.png", "wb") as f:
        f.write(png_bytes)
        
    print("Graph saved successfully to itinerary_graph_v2.png!")