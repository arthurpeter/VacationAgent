from langchain_core.tools import tool
from duckduckgo_search import DDGS

from app.core.logger import get_logger

log = get_logger(__name__)

@tool
def web_search_tool(query: str) -> str:
    """
    Search the internet for real-time information and historical data.
    Use this to find:
    1. Current events and live weather.
    2. Typical climate, average temperatures, and rainfall for future months.
    3. Travel advisories, peak tourist seasons, and general destination facts.
    Input should be a highly specific search engine query.
    """   
    log.info(f"Performing web search for query: {query}")
    try:
        results = DDGS().text(query, max_results=3)
        
        if not results:
            return "No search results found for that query."

        snippets = [res["body"] for res in results]
        
        combined_text = " ".join(snippets)
        
        safe_result = combined_text[:1000] 
        
        return safe_result
        
    except Exception as e:
        log.error(f"Error during web search: {e}")
        return f"Web search failed. Proceed with existing knowledge. Error: {str(e)}"

responder_tools = [web_search_tool]