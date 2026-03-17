from langgraph.graph import START, END, StateGraph
from langgraph.store.memory import InMemoryStore
from app.services.agents.memory import DiscoveryState
from app.services.agents.nodes import information_collector, should_get_more_info
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from psycopg_pool import ConnectionPool
from dotenv import load_dotenv
import os

load_dotenv()

def generate_graph():
    
    builder = StateGraph(DiscoveryState)
    builder.add_node("information_collector", information_collector)

    builder.add_edge(START, "information_collector")
    builder.add_edge("information_collector", END)

    return builder.compile()


if __name__ == "__main__":
    print("This module is not meant to be run directly. It provides the execution graph.\n\n")
    print("Test\n\n")
    print("=======================================================================\n\n")
    
    import asyncio
    from langchain_core.messages import HumanMessage
    from app.core.database import SessionLocal
    
    # Assuming get_initial_state is in your utils file based on your previous snippets
    from app.services.agents.utils import get_initial_state

    async def main_test():
        print("=======================================================================")
        print("Test: Information Collector Node")
        print("=======================================================================\n")
        
        graph = generate_graph()
        
        # ⚠️ CRITICAL: Set this to a real session_id that exists in your database
        test_session_id = 2 
        
        print(f"Fetching state for session {test_session_id} using async DB connection...")
        
        # Async DB connection scope
        async with SessionLocal() as db:
            try:
                state = await get_initial_state(db, test_session_id)
            except Exception as e:
                print(f"❌ Database Error: {e}")
                return

        # Add the test user message
        user_message = "We decided to change our destination to Tokyo and we are bringing our 5-year-old son."
        state["messages"].append(HumanMessage(content=user_message))
        
        print(f"\nUser Query: '{user_message}'")
        print("Invoking graph...\n")

        # Run the graph asynchronously
        result = await graph.ainvoke(state)

        print("=== EXTRACTED DATA OUTPUT ===")
        new_data = result.get("newly_extracted_data", {})
        if new_data:
            for key, value in new_data.items():
                if value is not None:
                    print(f"- {key}: {value}")
        else:
            print("No new data extracted.")
        print("\n=======================================================================\n")

    # Run the async test
    asyncio.run(main_test())