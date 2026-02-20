from typing import Optional
import requests
import os
from dotenv import load_dotenv
import json
from app.core.cache import redis_cache

load_dotenv()

# --- API Configuration ---
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")
RAPIDAPI_HOST = "booking-com15.p.rapidapi.com"

REQUEST_TIMEOUT = 30 # seconds

if not RAPIDAPI_KEY:
    print("Error: RAPIDAPI_KEY not found. Please create a .env file with your key.")
    exit()

@redis_cache(expire_time=3600 * 24 * 7)
def get_destination_id(location_name: str) -> dict:
    """
    Calls the /api/v1/hotels/searchDestination endpoint.
    
    Args:
        location_name (str): The name of the city/location.
    
    Returns:
        dict: The first destination object found (or None).
    """
    url = f"https://{RAPIDAPI_HOST}/api/v1/hotels/searchDestination"
    
    querystring = {"query": location_name}
    headers = {
        "x-rapidapi-key": RAPIDAPI_KEY,
        "x-rapidapi-host": RAPIDAPI_HOST
    }
    
    print(f"Calling searchDestination for '{location_name}'...")
    try:
        response = requests.get(url, headers=headers, params=querystring, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        results = response.json()
        
        if results.get("status") and results.get("data"):
            # Return the first and most relevant destination ID
            return results["data"][0]
        else:
            print(f"Could not find a valid destination in response: {results}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"Error during destination search: {e}")
        if response:
            print(f"Response body: {response.text}")
        return None

# change to 5 - 15 minutes in prod
@redis_cache(expire_time=3600 * 24)
def search_hotels(
        dest_id: str,
        search_type: str,
        arrival_date: str,
        departure_date: str,
        currency_code: str,
        adults: Optional[int]=None,
        children: Optional[str]=None,
        room_qty: Optional[int]=None,
        price_min: Optional[int]=None,
        price_max: Optional[int]=None,
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
    
    # These are query parameters for a GET request
    querystring = {
        "dest_id": dest_id,
        "search_type": search_type.upper(),
        "arrival_date": arrival_date,
        "departure_date": departure_date,
        "languagecode": "en-us",
        currency_code: currency_code.upper()
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

    headers = {
        "x-rapidapi-key": RAPIDAPI_KEY,
        "x-rapidapi-host": RAPIDAPI_HOST
    }

    try:
        response = requests.get(url, headers=headers, params=querystring, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()  # Raises an HTTPError for bad responses
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error during hotel search: {e}")
        if response:
            print(f"Response body: {response.text}")
        return {}

 # change to 5 - 15 minutes in prod 
@redis_cache(expire_time=3600 * 24)
def get_hotel_details(
        hotel_id: str,
        arrival_date: str,
        departure_date: str,
        currency_code: str,
        adults: Optional[int]=None,
        children: Optional[str]=None,
        room_qty: Optional[int]=None
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
        "currency_code": currency_code.upper()
    }

    if adults is not None:
        querystring["adults"] = adults

    if children is not None:
        querystring["children"] = children

    if room_qty is not None:
        querystring["room_qty"] = room_qty
    
    headers = {
        "x-rapidapi-key": RAPIDAPI_KEY,
        "x-rapidapi-host": RAPIDAPI_HOST
    }

    try:
        response = requests.get(url, headers=headers, params=querystring, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()  # Raises an HTTPError for bad responses
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error during hotel details fetch: {e}")
        if response:
            print(f"Response body: {response.text}")
        return {}

def main():
    """
    Runs the full workflow:
    1. Get Destination ID for the location.
    2. Search for hotels using that ID.
    3. Find the cheapest hotel from the list.
    4. Get the details for that cheapest hotel.
    5. Print the direct booking link.
    """
    
    LOCATION = "Paris, France"
    CHECKIN_DATE = "2026-05-10"
    CHECKOUT_DATE = "2026-05-17"

    print(f"Step 1: Getting Destination ID for '{LOCATION}'...")
    
    destination = get_destination_id(LOCATION)
    
    if not destination or "dest_id" not in destination or "search_type" not in destination:
        print("Could not get a valid destination ID. Exiting.")
        return
        
    dest_id = destination["dest_id"]
    search_type = destination["search_type"]
    
    print(f"Found Destination ID: {dest_id} (Type: {search_type})")

    print(f"Step 2: Searching for hotels...")
    search_results = search_hotels(dest_id, search_type, CHECKIN_DATE, CHECKOUT_DATE)
    
    print(json.dumps(search_results, indent=2))
    
    if not search_results or not search_results.get("status"):
        print("Search API call failed.")
        if search_results:
            print(f"API Error Message: {search_results.get('message', 'No message provided.')}")
            print(f"Full Response: {json.dumps(search_results, indent=2)}")
        return

    hotels_list = search_results.get("data", {}).get("hotels")
    if not hotels_list:
        print("No hotels found for this search.")
        return
        
    print(f"Found {len(hotels_list)} hotels. Finding the cheapest one...")

    cheapest_hotel = None
    min_price = float('inf')

    for hotel in hotels_list:
        property_data = hotel.get("property")
        if not property_data:
            continue

        try:
            price_breakdown = property_data.get("priceBreakdown", {})
            gross_price = price_breakdown.get("grossPrice", {})
            price_value = gross_price.get("value")

            if price_value is None:
                raise ValueError("Price value is None")

            price_value = float(price_value)
            
            if price_value < min_price:
                min_price = price_value
                cheapest_hotel = hotel
        except (KeyError, TypeError, ValueError, AttributeError) as e:
            continue
            
    if not cheapest_hotel:
        print("Could not find any hotels with a valid price.")
        return
        
    hotel_id = cheapest_hotel.get("hotel_id")
    hotel_name = cheapest_hotel.get("property", {}).get("name")
    
    print(f"\nStep 3: Found cheapest hotel:")
    print(f"  Name: {hotel_name}")
    print(f"  Price: ${min_price}")
    print(f"  Hotel ID: {hotel_id}")
    
    print(f"Getting details and booking link for {hotel_name}...")
    details_response = get_hotel_details(hotel_id, CHECKIN_DATE, CHECKOUT_DATE)
    
    if not details_response or not details_response.get("status"):
        print("Details API call failed.")
        if details_response:
            print(f"API Error Message: {details_response.get('message', 'No message provided.')}")
            print(f"Full Response: {json.dumps(details_response, indent=2)}")
        return
        
    booking_link = details_response.get("data", {}).get("url")
    
    if booking_link:
        print("\n--- ✅ SUCCESS! ---")
        print(f"Direct Booking.com Link:\n{booking_link}")
    else:
        print("Error: Could not find 'hotelUrl' in the details response.")
        print("Full details response:")
        print(json.dumps(details_response, indent=2))


if __name__ == "__main__":
    main()