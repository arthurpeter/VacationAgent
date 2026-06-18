import httpx
import asyncio
from datetime import datetime, time, timedelta
from typing import Optional, Dict, Any, Tuple
from app.core.config import settings
from app.core.logger import get_logger
from app.core.cache import redis_cache

log = get_logger(__name__)


def get_normalized_departure_datetime(
    time_str: str, is_weekend: bool = False
) -> datetime:
    """
    Normalizes time strings into 4 stable structural timestamp anchors.
    Forces the target to be 1 week after the next upcoming Tuesday/Saturday
    to ensure compatibility with a 7-day Redis cache expiration window.
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
        days_ahead = (5 - now.weekday()) % 7
    else:
        days_ahead = (1 - now.weekday()) % 7

    if days_ahead == 0 and now.time() > target_time:
        days_ahead += 7

    days_ahead += 7

    target_date = now + timedelta(days=days_ahead)
    return datetime.combine(target_date.date(), target_time)


@redis_cache(expire_time=60 * 60 * 24 * 7)
async def fetch_google_directions(
    origin_coords: Tuple[float, float],
    destination_coords: Tuple[float, float],
    mode: str,
    normalized_dt: datetime,
    origin_name: Optional[str] = None,
    destination_name: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """
    Fetches real-world navigation metadata between precise coordinates.
    Returns a minimized, high-fidelity payload optimized for React rendering and Redis space.
    """
    origin = origin_name if origin_name else f"{origin_coords[0]},{origin_coords[1]}"
    destination = (
        destination_name
        if destination_name
        else f"{destination_coords[0]},{destination_coords[1]}"
    )

    timestamp = int(normalized_dt.timestamp())

    url = "https://maps.googleapis.com/maps/api/directions/json"
    params = {
        "origin": origin,
        "destination": destination,
        "mode": mode,
        "departure_time": timestamp,
        "key": settings.GOOGLE_API_KEY,
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

            route = data["routes"][0]
            leg = route["legs"][0]

            parsed_bundle = {
                "status": "verified",
                "mode": mode,
                "distance_text": leg["distance"]["text"],
                "duration_mins": int(
                    leg.get("duration_in_traffic", leg["duration"])["value"] // 60
                ),
                "polyline": route["overview_polyline"]["points"],
                "transfers": 0,
                "steps": [],
            }

            for step in leg.get("steps", []):
                clean_instruction = (
                    step["html_instructions"]
                    .replace("\u202f", " ")
                    .replace("&nbsp;", " ")
                )

                step_data = {
                    "travel_mode": step["travel_mode"].lower(),
                    "duration_mins": int(step["duration"]["value"] // 60),
                    "instruction": clean_instruction,
                }

                if "transit_details" in step:
                    parsed_bundle["transfers"] += 1
                    details = step["transit_details"]
                    line = details["line"]

                    step_data["transit_detail"] = {
                        "line_name": line.get(
                            "short_name", line.get("name", "Transit")
                        ),
                        "vehicle_type": line["vehicle"]["type"].lower(),
                        "num_stops": details["num_stops"],
                        "departure_stop": details["departure_stop"]["name"],
                        "arrival_stop": details["arrival_stop"]["name"],
                        "bg_color": line.get("color", "#2563eb"),
                        "text_color": line.get("text_color", "#ffffff"),
                    }

                parsed_bundle["steps"].append(step_data)

            if parsed_bundle["transfers"] > 0:
                parsed_bundle["transfers"] -= 1

            return parsed_bundle

        except Exception as e:
            log.error(f"Critical execution block trap in direction resolver: {e}")
            return None


async def get_transit_bundle_for_leg(
    origin_coords: Tuple[float, float],
    destination_coords: Tuple[float, float],
    time_str: str,
    is_weekend: bool,
    driving_enabled: bool = False,
    origin_name: Optional[str] = None,
    destination_name: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Orchestrates parallel routing queries based on user mobility configuration rules.
    Restricts active processing modes to minimize Google API resource usage.
    """

    normalized_dt = get_normalized_departure_datetime(time_str, is_weekend)

    bundle = {}

    if driving_enabled:
        driving_data = await fetch_google_directions(
            origin_coords,
            destination_coords,
            "driving",
            normalized_dt,
            origin_name,
            destination_name,
        )
        if driving_data:
            bundle["driving"] = driving_data
        return bundle

    transit_task = fetch_google_directions(
        origin_coords,
        destination_coords,
        "transit",
        normalized_dt,
        origin_name,
        destination_name,
    )
    driving_task = fetch_google_directions(
        origin_coords,
        destination_coords,
        "driving",
        normalized_dt,
        origin_name,
        destination_name,
    )

    transit_data, driving_data = await asyncio.gather(transit_task, driving_task)

    if transit_data:
        bundle["transit"] = transit_data

    if driving_data:
        uber_data = dict(driving_data)
        uber_data["mode"] = "uber"
        uber_data["duration_mins"] = driving_data["duration_mins"] + 5

        bundle["uber"] = uber_data

    return bundle


if __name__ == "__main__":

    async def test_cache_hits():
        print("--- Testing Caching Behavior with Shifting Time Strings ---")

        colosseum = (41.8902, 12.4922)
        vatican = (41.9060, 12.4546)

        time_version_1 = "14:10"
        time_version_2 = "14:20"

        dt_1 = get_normalized_departure_datetime(time_version_1, is_weekend=False)
        dt_2 = get_normalized_departure_datetime(time_version_2, is_weekend=False)

        print(f"Time 1 ({time_version_1}) normalizes to target timestamp: {dt_1}")
        print(f"Time 2 ({time_version_2}) normalizes to target timestamp: {dt_2}")
        print(f"Are the target datetimes identical? {dt_1 == dt_2} <-- SUCCESS!")

        print("\nFiring Request 1 (Cache MISS)...")
        response = await fetch_google_directions(colosseum, vatican, "transit", dt_1)
        print(f"Response for Request 1: {response}")

    asyncio.run(test_cache_hits())
