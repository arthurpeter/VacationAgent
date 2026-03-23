import orjson
import sys
import asyncio
import os
from dotenv import load_dotenv

from langgraph.graph import START, END, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langchain_core.messages import HumanMessage
from psycopg_pool import AsyncConnectionPool
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.agents.memory import DiscoveryState
from app.services.agents.nodes import information_collector, db_validator, responder
from app.services.agents.utils import get_initial_state, get_resumed_state
from app.services.agents.tools import responder_tools
from app.core.database import SessionLocal, langgraph_pool
from app.core.logger import get_logger

load_dotenv()

log = get_logger(__name__)

def generate_graph(checkpointer=None):
    
    builder = StateGraph(DiscoveryState)
    builder.add_node("information_collector", information_collector)
    builder.add_node("db_validator", db_validator)
    builder.add_node("responder", responder)
    builder.add_node("tools", ToolNode(responder_tools))

    builder.add_edge(START, "information_collector")
    builder.add_edge("information_collector", "db_validator")
    builder.add_edge("db_validator", "responder")
    builder.add_conditional_edges(
        "responder", 
        tools_condition 
    )
    builder.add_edge("tools", "responder")

    return builder.compile(checkpointer=checkpointer)

async def stream_discovery_message(
    session_id: int, 
    user_message: str, 
    db: AsyncSession, 
    checkpointer: AsyncPostgresSaver
):
    graph = generate_graph(checkpointer) 
    config = {"configurable": {"thread_id": str(session_id)}}

    current_state = await graph.aget_state(config)

    if not current_state.values:
        log.info(f"Starting new LangGraph thread for session {session_id}...")
        input_data = await get_initial_state(db, session_id)
        input_data["messages"].append(HumanMessage(content=user_message))
    else:
        log.info(f"Resuming existing thread for session {session_id}...")
        fresh_extracted_data = await get_resumed_state(db, session_id)
        input_data = {
            "messages": [HumanMessage(content=user_message)],
            "extracted_data": fresh_extracted_data
        }

    final_ai_text = ""

    async for event in graph.astream(input_data, config=config, stream_mode="updates"):
        for node_name, node_updates in event.items():
            
            new_messages = node_updates.get("messages", [])
            if new_messages:
                last_msg = new_messages[-1] if isinstance(new_messages, list) else new_messages
                if getattr(last_msg, "type", "") == "ai":
                    final_ai_text = last_msg.content
            
            state_changes = node_updates.get("extracted_data", {})
            
            payload = {
                "status": "processing",
                "current_node": node_name,
                "extracted_data": state_changes,
            }
            
            yield f"data: {orjson.dumps(payload).decode()}\n\n"

    final_payload = {
        "status": "complete", 
        "ai_message": final_ai_text
    }
    yield f"data: {orjson.dumps(final_payload).decode()}\n\n"



if __name__ == "__main__":
    print("This module is not meant to be run directly. It provides the execution graph.\n\n")
    print("Test\n\n")
    my_graph = generate_graph()
    
    png_bytes = my_graph.get_graph(xray=True).draw_mermaid_png()
    
    with open("discovery_graph_v1.png", "wb") as f:
        f.write(png_bytes)
        
    print("Graph saved successfully to discovery_graph_v1.png!")