import pprint

import orjson

from langgraph.graph import START, END, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langchain_core.messages import HumanMessage
from langgraph.types import Send
from psycopg_pool import AsyncConnectionPool
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.agents.memory import ItineraryState
from app.services.agents.nodes import *
from app.services.agents.utils import get_initial_itinerary_state
from app.services.agents.tools import link_finder_tools, detailer_tools
from app.core.logger import get_logger

log = get_logger(__name__)

def route_stage(state: ItineraryState):
    """Routes the graph from START based on the current stage of the funnel."""
    stage = state.get("stage", 0)
    
    if stage == 0:
        return "picking_attractions"
    elif stage == 1:
        return "picking_transit"
    elif stage == 2:
        return "organizing_days"
    elif stage == 3:
        return "organizing_attractions"
    else:
        return "picking_attractions"
    
def route_unresolved_attractions(state: ItineraryState):
    action = state.get("action")
    unresolved = state.get("unresolved_attractions", [])
    
    if action == "resolve_attractions" and len(unresolved) > 0:
        return [Send("enrich_single_attraction_node", poi) for poi in unresolved]
        
    return END

def generate_graph(checkpointer=None):
    
    builder = StateGraph(ItineraryState)

    builder.add_node("picking_attractions", picking_attractions)
    builder.add_node("picking_transit", picking_transit)
    builder.add_node("organizing_days", organizing_days)
    builder.add_node("organizing_attractions", organizing_attractions)

    builder.add_node("enrich_single_attraction_node", enrich_single_attraction_node)
    builder.add_node("save_attractions_to_db", save_attractions_to_db)

    builder.add_conditional_edges(START, route_stage, {
        "picking_attractions": "picking_attractions",
        "picking_transit": "picking_transit",
        "organizing_days": "organizing_days",
        "organizing_attractions": "organizing_attractions"
    })

    builder.add_conditional_edges(
        "picking_attractions",
        route_unresolved_attractions,
        {
            "enrich_single_attraction_node": "enrich_single_attraction_node",
            END: END
        }
    )
    
    builder.add_edge("enrich_single_attraction_node", "save_attractions_to_db")
    builder.add_edge("save_attractions_to_db", END)
    builder.add_edge("picking_transit", END)
    builder.add_edge("organizing_days", END)
    builder.add_edge("organizing_attractions", END)

    return builder.compile(checkpointer=checkpointer)

async def run_itinerary_graph(
    session_id: int,
    action: str,
    stage: int,
    query: Optional[str],
    db: AsyncSession,
    checkpointer: AsyncPostgresSaver
) -> dict:
    """
    Executes the itinerary graph to completion for a specific action and stage.
    Returns the full final state of the graph.
    """
    graph = generate_graph(checkpointer)
    config = {"configurable": {"thread_id": f"itinerary_{session_id}"}}

    current_state = await graph.aget_state(config)

    if not current_state.values:
        log.info(f"Initializing new itinerary state for session {session_id}...")
        input_data = await get_initial_itinerary_state(db, session_id)
    else:
        log.info(f"Resuming itinerary state for session {session_id}...")
        input_data = {}

    input_data["action"] = action
    input_data["stage"] = stage
    
    if query:
        input_data["messages"] = [HumanMessage(content=query)]

    final_state = await graph.ainvoke(input_data, config=config)
    
    return final_state

# import asyncio

if __name__ == "__main__":
    print("This module is not meant to be run directly. It provides the execution graph for the itinerary process.\n\n")
    my_graph = generate_graph()
    
    png_bytes = my_graph.get_graph(xray=True).draw_mermaid_png()
    
    with open("itinerary_graph_v2.png", "wb") as f:
        f.write(png_bytes)
        
    print("Graph saved successfully to itinerary_graph_v2.png!")

    # async def test_initial_fetch():
    #     print("🚀 Compiling the Itinerary Graph...")
    #     graph = generate_graph()

    #     initial_state = {
    #         "stage": 0,
    #         "action": "initial_fetch",
    #         "data": {
    #             "destination": "Rome, It"
    #         },
    #         "persona": "History Buff",
    #         "pois": [],
    #         "unresolved_attractions": [],
    #         "resolved_attractions": [],
    #         "messages": []
    #     }

    #     print(f"🌍 Starting graph execution for {initial_state['data']['destination']}...")

    #     final_state = await graph.ainvoke(initial_state)

    #     print("\n✅ Graph Execution Finished!\n")

    #     print("--- Final POIs Collected ---")
    #     pprint.pprint(final_state.get("pois"))

    #     print("\n--- Final Graph State Keys ---")
    #     print(f"Action: {final_state.get('action')}")
    #     print(f"Unresolved Count: {len(final_state.get('unresolved_attractions', []))}")
    #     print(f"Resolved Count: {len(final_state.get('resolved_attractions', []))}")

    # asyncio.run(test_initial_fetch())