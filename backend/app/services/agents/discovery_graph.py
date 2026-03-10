from langgraph.graph import START, END, StateGraph
from langgraph.store.memory import InMemoryStore
from app.services.agents.memory import DiscoveryState
from backend.app.services.agents.nodes import information_collector, should_get_more_info
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from psycopg_pool import ConnectionPool
from dotenv import load_dotenv
import os

load_dotenv()

def next_node(state):
    return state

def generate_graph(memory: InMemoryStore):
    
    builder = StateGraph(DiscoveryState)
    builder.add_node("information_collector", information_collector)
    builder.add_node("next_node", next_node)

    builder.add_edge(START, "information_collector")
    builder.add_conditional_edges("information_collector", should_get_more_info, ["next_node", END])
    builder.add_edge("next_node", END)


if __name__ == "__main__":
    print("This module is not meant to be run directly. It provides the execution graph.\n\n")
    print("Test\n\n")
    print("=======================================================================\n\n")

