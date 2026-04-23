import time
import random
import threading

from langchain_core.tools import tool
from ddgs import DDGS

from app.core.logger import get_logger

log = get_logger(__name__)

ddgs_lock = threading.Lock()

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
    
    max_retries = 3
    base_delay = 2.0
    
    with ddgs_lock:
        for attempt in range(max_retries):
            try:
                if attempt == 0:
                    time.sleep(random.uniform(1.0, 2.0))
                    
                results = DDGS().text(query, max_results=3)
                
                if not results:
                    return "No search results found for that query."

                snippets = [res["body"] for res in results]
                
                combined_text = " ".join(snippets)
                
                safe_result = combined_text[:1000] 

                log.info(f"Web search successful. Returning combined snippets: {safe_result[:100]}")
                return safe_result
                
            except Exception as e:
                error_msg = str(e).lower()
                if "rate limit" in error_msg or "202" in error_msg or "timeout" in error_msg or "httpx" in error_msg:
                    log.warning(f"DDGS Rate limit/Network error for '{query}'. Attempt {attempt + 1}/{max_retries}. Retrying in {base_delay}s...")
                    time.sleep(base_delay)
                    base_delay *= 2
                else:
                    log.error(f"Error during web search: {e}")
                    return f"Web search failed. Proceed with existing knowledge. Error: {str(e)}"
                    
        log.error(f"Web search failed after {max_retries} attempts due to rate limits.")
        return "Web search failed due to search engine rate limits. Proceed with existing knowledge."

responder_tools = [web_search_tool]

@tool
def link_finder_tool(query: str) -> str:
    """
    Given a user query, find relevant links to official tourism sites, local event calendars, or travel advisory pages.
    This is meant to provide the user with direct access to authoritative resources for their trip planning.
    """
    log.info(f"Finding links for query: {query}")
    
    max_retries = 3
    base_delay = 2.0
    
    with ddgs_lock:
        for attempt in range(max_retries):
            try:
                if attempt == 0:
                    time.sleep(random.uniform(1.0, 2.0))
                
                results = DDGS().text(query, max_results=5)
                
                if not results:
                    return "No relevant links found for that query."
                
                links = {res["href"]: res.get("title", "No title available") for res in results if "href" in res}
                
                if not links:
                    return "No relevant links found for that query."
                
                combined_links = "\n".join([f"{url}: {description}" for url, description in links.items()])
                
                log.info(f"Link finding successful. Returning links: {combined_links}")
                return combined_links
                
            except Exception as e:
                error_msg = str(e).lower()
                if "rate limit" in error_msg or "202" in error_msg or "timeout" in error_msg or "httpx" in error_msg:
                    log.warning(f"DDGS Rate limit/Network error for '{query}'. Attempt {attempt + 1}/{max_retries}. Retrying in {base_delay}s...")
                    time.sleep(base_delay)
                    base_delay *= 2
                else:
                    log.error(f"Error during link finding: {e}")
                    return f"Link finding failed. Proceed with existing knowledge. Error: {str(e)}"
                    
        log.error(f"Link finding failed after {max_retries} attempts due to rate limits.")
        return "Link finding failed due to search engine rate limits. Proceed with existing knowledge and skip finding links for this item."

link_finder_tools = [link_finder_tool]