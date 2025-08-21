from langgraph.graph import START, END, StateGraph
from langgraph.store.memory import InMemoryStore
from app.services.agents.memory import GraphMemory, State
from app.services.agents.agents import information_collector

def generate_graph(memory: InMemoryStore):
    
    builder = StateGraph(State)
    builder.add_node(information_collector, "Collect Information")

    builder.add_edge(START, information_collector)

    graph = builder.compile(store=memory)

    return graph

