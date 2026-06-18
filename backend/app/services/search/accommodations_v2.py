from typing import Optional
import httpx
from app.core.config import settings
from app.core.cache import redis_cache


RAPIDAPI_KEY = settings.RAPIDAPI_KEY
RAPIDAPI_HOST = "booking-com15.p.rapidapi.com"

REQUEST_TIMEOUT = 60

if not RAPIDAPI_KEY:
    print("Error: RAPIDAPI_KEY not found. Please create a .env file with your key.")
    exit()


@redis_cache(expire_time=3600 * 24 * 14)
async def get_destination_id(location_name: str) -> dict:
    """
    Calls the /api/v1/hotels/searchDestination endpoint.

    Args:
        location_name (str): The name of the city/location.

    Returns:
        dict: The first destination object found (or None).
    """
    url = f"https://{RAPIDAPI_HOST}/api/v1/hotels/searchDestination"

    querystring = {"query": location_name}
    headers = {"x-rapidapi-key": RAPIDAPI_KEY, "x-rapidapi-host": RAPIDAPI_HOST}

    print(f"Calling searchDestination for '{location_name}'...")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                url,
                headers=headers,
                params=querystring,
                timeout=REQUEST_TIMEOUT,
            )
        response.raise_for_status()
        results = response.json()

        if results.get("status") and results.get("data"):
            return results["data"][0]
        else:
            print(f"Could not find a valid destination in response: {results}")
            return None
    except httpx.HTTPError as e:
        print(f"Error during destination search: {e}")
        if response:
            print(f"Response body: {response.text}")
        return None


@redis_cache(expire_time=3600 * 24 * 14)
async def search_hotels(
    dest_id: str,
    search_type: str,
    arrival_date: str,
    departure_date: str,
    currency_code: str,
    adults: Optional[int] = None,
    children: Optional[str] = None,
    room_qty: Optional[int] = None,
    price_min: Optional[int] = None,
    price_max: Optional[int] = None,
) -> dict:
    """
    Calls the /api/v1/hotels/searchHotels endpoint.
    This is a GET request, not POST.

    Args:
        dest_id (str): The destination ID from get_destination_id.
        search_type (str): The search type from get_destination_id (e.g., "CITY").
        arrival_date (str): YYYY-MM-DD
        departure_date (str): YYYY-MM-DD

    Returns:
        dict: The JSON response from the API.
    """
    url = f"https://{RAPIDAPI_HOST}/api/v1/hotels/searchHotels"

    querystring = {
        "dest_id": dest_id,
        "search_type": search_type.upper(),
        "arrival_date": arrival_date,
        "departure_date": departure_date,
        "languagecode": "en-us",
        currency_code: currency_code.upper(),
    }

    if adults is not None:
        querystring["adults"] = adults

    if children is not None:
        querystring["children"] = children

    if room_qty is not None:
        querystring["room_qty"] = room_qty

    if price_min is not None:
        querystring["price_min"] = price_min

    if price_max is not None:
        querystring["price_max"] = price_max

    headers = {"x-rapidapi-key": RAPIDAPI_KEY, "x-rapidapi-host": RAPIDAPI_HOST}

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                url,
                headers=headers,
                params=querystring,
                timeout=REQUEST_TIMEOUT,
            )
        response.raise_for_status()
        return response.json()
    except httpx.HTTPError as e:
        print(f"Error during hotel search: {e}")
        if response:
            print(f"Response body: {response.text}")
        return {}


@redis_cache(expire_time=3600 * 24 * 14)
async def get_hotel_details(
    hotel_id: str,
    arrival_date: str,
    departure_date: str,
    currency_code: str,
    adults: Optional[int] = None,
    children: Optional[str] = None,
    room_qty: Optional[int] = None,
) -> dict:
    """
    Calls the /api/v1/hotels/getHotelDetails endpoint.

    Args:
        hotel_id (str): The ID of the hotel.
        arrival_date (str): The arrival date (YYYY-MM-DD).
        departure_date (str): The departure date (YYYY-MM-DD).

    Returns:
        dict: The JSON response from the API.
    """
    url = f"https://{RAPIDAPI_HOST}/api/v1/hotels/getHotelDetails"

    querystring = {
        "hotel_id": hotel_id,
        "arrival_date": arrival_date,
        "departure_date": departure_date,
        "languagecode": "en-us",
        "currency_code": currency_code.upper(),
    }

    if adults is not None:
        querystring["adults"] = adults

    if children is not None:
        querystring["children"] = children

    if room_qty is not None:
        querystring["room_qty"] = room_qty

    headers = {"x-rapidapi-key": RAPIDAPI_KEY, "x-rapidapi-host": RAPIDAPI_HOST}

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                url,
                headers=headers,
                params=querystring,
                timeout=REQUEST_TIMEOUT,
            )
        response.raise_for_status()
        return response.json()
    except httpx.HTTPError as e:
        print(f"Error during hotel details fetch: {e}")
        if response:
            print(f"Response body: {response.text}")
        return {}
