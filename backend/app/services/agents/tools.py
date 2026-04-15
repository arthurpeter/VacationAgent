from langchain_core.tools import tool
from ddgs import DDGS

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

        log.info(f"Web search successful. Returning combined snippets: {safe_result[:100]}")
        
        return safe_result
        
    except Exception as e:
        log.error(f"Error during web search: {e}")
        return f"Web search failed. Proceed with existing knowledge. Error: {str(e)}"

responder_tools = [web_search_tool]

@tool
def link_finder_tool(query: str) -> str:
    """
    Given a user query, find relevant links to official tourism sites, local event calendars, or travel advisory pages.
    This is meant to provide the user with direct access to authoritative resources for their trip planning.
    """
    log.info(f"Finding links for query: {query}")
    try:
        results = DDGS().text(query, max_results=5)
        
        if not results:
            return "No relevant links found for that query."
        
        # link -> description mapping (if available)
        links = {res["href"]: res.get("title", "No title available") for res in results if "href" in res}

        
        if not links:
            return "No relevant links found for that query."
        
        combined_links = "\n".join([f"{url}: {description}" for url, description in links.items()])
        
        log.info(f"Link finding successful. Returning links: {combined_links}")
        
        return combined_links
        
    except Exception as e:
        log.error(f"Error during link finding: {e}")
        return f"Link finding failed. Proceed with existing knowledge. Error: {str(e)}"
    
link_finder_tools = [link_finder_tool]