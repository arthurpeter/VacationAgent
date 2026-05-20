import httpx
import asyncio
from datetime import datetime, time, timedelta
from typing import Optional, Dict, Any, Tuple
from app.core.config import settings
from app.core.logger import get_logger
from app.core.cache import redis_cache

log = get_logger(__name__)

def get_normalized_departure_datetime(time_str: str, is_weekend: bool = False) -> datetime:
    """
    Normalizes time strings into 4 stable structural timestamp anchors.
    This MUST be called before passing data to the cached function.
    """
    try:
        parsed_time = datetime.strptime(time_str, "%H:%M").time()
    except ValueError:
        parsed_time = time(12, 0)

    if time(7, 0) <= parsed_time < time(9, 30):
        target_time = time(8, 0)
    elif time(9, 30) <= parsed_time < time(15, 30):
        target_time = time(12, 30)
    elif time(15, 30) <= parsed_time < time(19, 0):
        target_time = time(17, 30)
    else:
        target_time = time(20, 30)

    now = datetime.now()

    if is_weekend:
        days_ahead = (5 - now.weekday()) % 7   # next Saturday
    else:
        days_ahead = (1 - now.weekday()) % 7   # next Tuesday

    if days_ahead == 0 and now.time() > target_time:
        days_ahead = 7

    target_date = now + timedelta(days=days_ahead)
    return datetime.combine(target_date.date(), target_time)


@redis_cache(expire_time=86400)
async def fetch_google_directions(
    origin_coords: Tuple[float, float], 
    destination_coords: Tuple[float, float], 
    mode: str, 
    normalized_dt: datetime # <-- FIX: Cache key now generates from this stable datetime object!
) -> Optional[Dict[str, Any]]:
    """
    Fetches real-world navigation metadata between precise coordinates.
    The decorator generates keys based on normalized_dt, ensuring maximum cache HIT ratios.
    """
    origin = f"{origin_coords[0]},{origin_coords[1]}"
    destination = f"{destination_coords[0]},{destination_coords[1]}"
    
    timestamp = int(normalized_dt.timestamp())
    
    url = "https://maps.googleapis.com/maps/api/directions/json"
    params = {
        "origin": origin,
        "destination": destination,
        "mode": mode,
        "departure_time": timestamp,
        "key": settings.GOOGLE_API_KEY
    }
    
    if mode == "driving":
        params["traffic_model"] = "best_guess"

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, params=params, timeout=10.0)
            if response.status_code != 200:
                log.error(f"Google Maps HTTP error: {response.status_code}")
                return None
                
            data = response.json()
            if data.get("status") != "OK":
                log.error(f"Google Maps API error status: {data.get('status')}")
                return None
            
            print(f"Google Maps API response for {mode} from {origin} to {destination} at {normalized_dt}: {data}")
                
            route = data["routes"][0]
            leg = route["legs"][0]
            
            parsed_bundle = {
                "status": "verified",
                "mode": mode,
                "distance_text": leg["distance"]["text"],
                "duration_mins": int(leg.get("duration_in_traffic", leg["duration"])["value"] // 60),
                "polyline": route["overview_polyline"]["points"],
                "warnings": route.get("warnings", []),
                "steps": []
            }
            
            for step in leg.get("steps", []):
                step_data = {
                    "travel_mode": step["travel_mode"],
                    "duration_mins": int(step["duration"]["value"] // 60),
                    "instruction": step["html_instructions"]
                }
                
                if "transit_details" in step:
                    details = step["transit_details"]
                    step_data["transit_detail"] = {
                        "line_name": details["line"].get("short_name", details["line"].get("name", "Transit")),
                        "vehicle_type": details["line"]["vehicle"]["type"],
                        "num_stops": details["num_stops"]
                    }
                    
                parsed_bundle["steps"].append(step_data)
                
            return parsed_bundle

        except Exception as e:
            log.error(f"Critical execution block trap in direction resolver: {e}")
            return None


# ----------------------------------------------------------------------
# CORRECT WORKFLOW TEST RUN
# ----------------------------------------------------------------------
if __name__ == "__main__":
    async def test_cache_hits():
        print("--- Testing Caching Behavior with Shifting Time Strings ---")
        
        colosseum = (41.8902, 12.4922)
        vatican = (41.9060, 12.4546)
        
        # Scenario: User moves an event by 10 minutes. 
        time_version_1 = "14:10"
        time_version_2 = "14:20"
        
        # 1. Normalize both times first
        dt_1 = get_normalized_departure_datetime(time_version_1, is_weekend=False)
        dt_2 = get_normalized_departure_datetime(time_version_2, is_weekend=False)
        
        print(f"Time 1 ({time_version_1}) normalizes to target timestamp: {dt_1}")
        print(f"Time 2 ({time_version_2}) normalizes to target timestamp: {dt_2}")
        print(f"Are the target datetimes identical? {dt_1 == dt_2} <-- SUCCESS!")
        
        print("\nFiring Request 1 (Cache MISS)...")
        await fetch_google_directions(colosseum, vatican, "transit", dt_1)
        
        print("\nFiring Request 2 (Should be a Cache HIT from Redis because dt_1 == dt_2)...")
        await fetch_google_directions(colosseum, vatican, "transit", dt_2)

    asyncio.run(test_cache_hits())