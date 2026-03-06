from langgraph.graph import START, END, StateGraph
from langgraph.store.memory import InMemoryStore
from app.services.agents.memory import State
from backend.app.services.agents.nodes import information_collector, should_get_more_info
from langgraph.checkpoint.postgres import PostgresSaver
from psycopg_pool import ConnectionPool
from dotenv import load_dotenv
import os

load_dotenv()

def next_node(state):
    return state

def generate_graph(memory: InMemoryStore):
    
    builder = StateGraph(State)
    builder.add_node("information_collector", information_collector)
    builder.add_node("next_node", next_node)  # Placeholder for the next node in the graph

    builder.add_edge(START, "information_collector")
    builder.add_conditional_edges("information_collector", should_get_more_info, ["next_node", END])
    builder.add_edge("next_node", END)

    with ConnectionPool(conninfo=os.getenv("DATABASE_URL")) as pool:
        checkpointer = PostgresSaver(pool)
        
        # IMPORTANT: Create the tables if they don't exist
        # This only needs to run once at startup
        checkpointer.setup()
        
        graph = builder.compile(checkpointer=checkpointer)
        return graph

if __name__ == "__main__":
    print("This module is not meant to be run directly. It provides the execution graph.\n\n")
    print("Test\n\n")
    print("=======================================================================\n\n")

    memory = InMemoryStore()
    graph = generate_graph(memory)

    img = graph.get_graph(xray=1).draw_mermaid_png()
    with open("graph.png", "wb") as f:
        f.write(img)
    print("Graph saved as graph.png")

    user_id = input("Enter user ID: ")

    while True:
        user_query = input("User: ")
        state = graph.invoke(State(user_query=user_query, user_id=user_id))
        print(f"State after invocation: {state}\n")
        if not state["need_information"]:
            print(memory.get(namespace="user_trip_information", key=user_id).value)
            continue

        print(state["llm_query"])
