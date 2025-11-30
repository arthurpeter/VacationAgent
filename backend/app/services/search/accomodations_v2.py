import requests
import os
from dotenv import load_dotenv
import json

# Load environment variables from .env file
load_dotenv()

# --- API Configuration ---
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")
RAPIDAPI_HOST = "booking-com15.p.rapidapi.com"

REQUEST_TIMEOUT = 30 # seconds

if not RAPIDAPI_KEY:
    print("Error: RAPIDAPI_KEY not found. Please create a .env file with your key.")
    exit()

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

def search_hotels(dest_id: str, search_type: str, checkin_date: str, checkout_date: str) -> dict:
    """
    Calls the /api/v1/hotels/searchHotels endpoint.
    This is a GET request, not POST.
    
    Args:
        dest_id (str): The destination ID from get_destination_id.
        search_type (str): The search type from get_destination_id (e.g., "CITY").
        checkin_date (str): YYYY-MM-DD
        checkout_date (str): YYYY-MM-DD
    
    Returns:
        dict: The JSON response from the API.
    """
    url = f"https://{RAPIDAPI_HOST}/api/v1/hotels/searchHotels"
    
    # These are query parameters for a GET request
    querystring = {
        "dest_id": dest_id,
        "search_type": search_type.upper(), 
        "arrival_date": checkin_date,
        "departure_date": checkout_date,
        "languagecode": "en-us",
        "currency_code": "USD",
        "adults": 2  
    }
    
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

def get_hotel_details(hotel_id: str, checkin_date: str, checkout_date: str) -> dict:
    """
    Calls the /api/v1/hotels/getHotelDetails endpoint.
    
    Args:
        hotel_id (str): The ID of the hotel.
        checkin_date (str): The check-in date (YYYY-MM-DD).
        checkout_date (str): The check-out date (YYYY-MM-DD).
    
    Returns:
        dict: The JSON response from the API.
    """
    url = f"https://{RAPIDAPI_HOST}/api/v1/hotels/getHotelDetails"
    
    querystring = {
        "hotel_id": hotel_id,
        "arrival_date": checkin_date,
        "departure_date": checkout_date,
        "languagecode": "en-us"
    }
    
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

# --- (FIXED) Main Function ---
def main():
    """
    Runs the full workflow:
    1. Get Destination ID for the location.
    2. Search for hotels using that ID.
    3. Find the cheapest hotel from the list.
    4. Get the details for that cheapest hotel.
    5. Print the direct booking link.
    """
    
    # --- 1. Define Search Parameters ---
    LOCATION = "Paris, France"
    # FIX 1: Use dates within the 1-year limit (e.g., 6 months from now)
    CHECKIN_DATE = "2026-05-10"
    CHECKOUT_DATE = "2026-05-17"

    print(f"Step 1: Getting Destination ID for '{LOCATION}'...")
    
    # --- 2. Call Destination API ---
    destination = get_destination_id(LOCATION)
    
    if not destination or "dest_id" not in destination or "search_type" not in destination:
        print("Could not get a valid destination ID. Exiting.")
        return
        
    dest_id = destination["dest_id"]
    search_type = destination["search_type"]
    
    print(f"Found Destination ID: {dest_id} (Type: {search_type})")

    # --- 3. Call Search API ---
    print(f"Step 2: Searching for hotels...")
    search_results = search_hotels(dest_id, search_type, CHECKIN_DATE, CHECKOUT_DATE)
    
    # --- ADDED: Print the full search result as requested ---
    print(json.dumps(search_results, indent=2))
    
    # FIX 2: Add better error printing to see the API's message
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

    # --- 4. Find Cheapest Hotel ---
    cheapest_hotel = None
    min_price = float('inf')

    for hotel in hotels_list:
        # --- FIX: All data is inside the 'property' sub-object ---
        property_data = hotel.get("property")
        if not property_data:
            continue # Skip if this hotel has no 'property' object
        # --- END FIX ---

        # Navigate the JSON path to get the price
        try:
            # Use .get() for safer dictionary access
            price_breakdown = property_data.get("priceBreakdown", {})
            gross_price = price_breakdown.get("grossPrice", {})
            price_value = gross_price.get("value") # Get value first

            if price_value is None:
                raise ValueError("Price value is None") # Trigger the except block

            price_value = float(price_value) # Now convert to float
            
            if price_value < min_price:
                min_price = price_value
                cheapest_hotel = hotel
        except (KeyError, TypeError, ValueError, AttributeError) as e:
            # Price parsing failed for this hotel, skip it
            continue
            
    if not cheapest_hotel:
        print("Could not find any hotels with a valid price.")
        return
        
    # --- FIX: Get id and name from the correct locations ---
    hotel_id = cheapest_hotel.get("hotel_id") # ID is at the top level
    hotel_name = cheapest_hotel.get("property", {}).get("name") # Name is inside 'property'
    
    print(f"\nStep 3: Found cheapest hotel:")
    print(f"  Name: {hotel_name}")
    print(f"  Price: ${min_price}")
    print(f"  Hotel ID: {hotel_id}")
    
    # --- 5. Call Details API ---
    print(f"Getting details and booking link for {hotel_name}...")
    details_response = get_hotel_details(hotel_id, CHECKIN_DATE, CHECKOUT_DATE)
    
    if not details_response or not details_response.get("status"):
        print("Details API call failed.")
        if details_response:
            print(f"API Error Message: {details_response.get('message', 'No message provided.')}")
            print(f"Full Response: {json.dumps(details_response, indent=2)}")
        return
        
    # --- 6. Print the Link ---
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