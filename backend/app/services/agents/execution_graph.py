from langgraph.graph import START, END, StateGraph
from langgraph.store.memory import InMemoryStore
from app.services.agents.memory import State
from app.services.agents.agents import information_collector, should_get_more_info

def next_node(state):
    return state

def generate_graph(memory: InMemoryStore):
    
    builder = StateGraph(State)
    builder.add_node("information_collector", information_collector)
    builder.add_node("next_node", next_node)  # Placeholder for the next node in the graph

    builder.add_edge(START, "information_collector")
    builder.add_conditional_edges("information_collector", should_get_more_info, ["next_node", END])
    builder.add_edge("next_node", END)

    graph = builder.compile(store=memory)

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
