import sys

from langgraph.graph import START, END, StateGraph
from langgraph.store.memory import InMemoryStore
from app.services.agents.memory import DiscoveryState
from app.services.agents.nodes import information_collector, should_get_more_info
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from psycopg_pool import ConnectionPool
from dotenv import load_dotenv
import os
from sqlalchemy.ext.asyncio import AsyncSession
from psycopg_pool import AsyncConnectionPool
import asyncio
from langchain_core.messages import HumanMessage
from app.core.database import SessionLocal
from app.services.agents.utils import get_initial_state
from app.core.database import SessionLocal
from app.core.config import settings

load_dotenv()

def generate_graph(checkpointer=None):
    
    builder = StateGraph(DiscoveryState)
    builder.add_node("information_collector", information_collector)

    builder.add_edge(START, "information_collector")
    builder.add_edge("information_collector", END)

    return builder.compile(checkpointer=checkpointer)

async def process_discovery_message(
    session_id: int, 
    user_message: str, 
    db: AsyncSession, 
    db_pool: AsyncConnectionPool
):
    """
    Dynamically routes the request.
    If no checkpoint exists, it builds the state from the DB.
    If a checkpoint exists, it appends the new message to memory.
    """
    checkpointer = AsyncPostgresSaver(db_pool)
    
    graph = generate_graph(checkpointer) 

    config = {"configurable": {"thread_id": str(session_id)}}

    current_state = await graph.aget_state(config)

    if not current_state.values:
        print(f"Starting new LangGraph thread for session {session_id}...")
        
        state = await get_initial_state(db, session_id)
        
        state["messages"].append(HumanMessage(content=user_message))
        
        result = await graph.ainvoke(state, config=config)
        
    else:
        print(f"Resuming existing thread for session {session_id}...")
        
        new_input = {"messages": [HumanMessage(content=user_message)]}
        
        result = await graph.ainvoke(new_input, config=config)

    return result


if __name__ == "__main__":
    print("This module is not meant to be run directly. It provides the execution graph.\n\n")
    print("Test\n\n")

    async def main_test():
        print("=======================================================================")
        print("Test: Information Collector Node")
        print("=======================================================================\n")
        
        raw_db_url = settings.DATABASE_URL.replace("+asyncpg", "").replace("+psycopg", "")

        async with AsyncConnectionPool(raw_db_url) as pool:
            
            async with SessionLocal() as db_session:
                
                result = await process_discovery_message(
                    session_id=1, 
                    user_message="I want to go to Paris from New York between September 10 and September 20. There will be 2 adults and 1 child. My budget is around $3000.",
                    db=db_session,
                    db_pool=pool
                )

                print("=== EXTRACTED DATA OUTPUT ===")
                new_data = result.get("newly_extracted_data", {})
                if new_data:
                    for key, value in new_data.items():
                        if value is not None:
                            print(f"- {key}: {value}")
                else:
                    print("No new data extracted.")
                print("\n=======================================================================\n")

    if sys.platform.startswith('win'):
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    asyncio.run(main_test())