from langgraph.graph import START, END, StateGraph
from app.utils.graph import generate_state_from_db

def generate_graph(uid: str):
    graph = StateGraph(generate_state_from_db(uid))
    return graph
