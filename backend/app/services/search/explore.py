import os
from serpapi import GoogleSearch
from typing import Dict, Any, Optional
from dotenv import load_dotenv
from app.core.cache import redis_cache

load_dotenv()

GoogleSearch.SERP_API_KEY = os.getenv('SERPAPI_API_KEY')
if not GoogleSearch.SERP_API_KEY:
    raise ValueError("SERPAPI_API_KEY environment variable is required")

@redis_cache(expire_time=3600 * 24)
def call_explore_api(
    departure_id: str,
    arrival_id: Optional[str] = None,
    arrival_area_id: Optional[str] = None,
    gl: Optional[str] = None,
    hl: Optional[str] = None,
    currency: Optional[str] = None,
    type: Optional[int] = None,
    outbound_date: Optional[str] = None,
    return_date: Optional[str] = None,
    month: Optional[int] = None,
    travel_duration: Optional[int] = None,
    travel_class: Optional[int] = None,
    stops: Optional[int] = None,
    adults: Optional[int] = None,
    children: Optional[int] = None,
    infants_in_seat: Optional[int] = None,
    infants_on_lap: Optional[int] = None,
    no_cache: Optional[bool] = None
) -> Dict[str, Any]:
    """
    Call the Google Travel Explore API via SerpAPI for "inspiration" searches.
    Uses the official serpapi-python library.
    """
    
    params = {
        "engine": "google_travel_explore",
        "departure_id": departure_id
    }
    
    optional_params = {
        "arrival_id": arrival_id,
        "arrival_area_id": arrival_area_id,
        "gl": gl,
        "hl": hl,
        "currency": currency,
        "type": type,
        "outbound_date": outbound_date,
        "return_date": return_date,
        "month": month,
        "travel_duration": travel_duration,
        "travel_class": travel_class,
        "stops": stops,
        "adults": adults,
        "children": children,
        "infants_in_seat": infants_in_seat,
        "infants_on_lap": infants_on_lap,
        "no_cache": no_cache
    }
    
    for key, value in optional_params.items():
        if value is not None:
            params[key] = value
            
    try:
        search = GoogleSearch(params)
        results = search.get_dict()
        
        if "error" in results:
            raise Exception(results["error"])
            
        return results
        
    except Exception as e:
        print(f"Error calling SerpAPI (Google Travel Explore): {e}")
        raise
