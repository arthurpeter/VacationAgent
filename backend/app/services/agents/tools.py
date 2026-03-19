from langchain_core.tools import tool

@tool
def dummy_search_tool(query: str) -> str:
    """A placeholder tool for searching the web for weather, locations, or travel facts."""
    print(f"--- FAKE EXECUTING TOOL FOR QUERY: {query} ---")
    return f"Search results for {query}: The weather is perfect, and the location is highly rated!"

responder_tools = [dummy_search_tool]