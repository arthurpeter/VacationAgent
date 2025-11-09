import os
from serpapi import GoogleSearch  # Import the official library
from typing import Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv()

# Set your API key globally from the .env file
# The GoogleSearch class will automatically use this.
GoogleSearch.SERP_API_KEY = os.getenv('SERPAPI_API_KEY')
if not GoogleSearch.SERP_API_KEY:
    raise ValueError("SERPAPI_API_KEY environment variable is required")

def call_flights_api(
    # Search Query (both optional)
    departure_id: Optional[str] = None,
    arrival_id: Optional[str] = None,
    # Localization
    gl: Optional[str] = None,
    hl: Optional[str] = None,
    currency: Optional[str] = None,
    # Advanced Google Flights Parameters
    type: Optional[int] = 1,
    outbound_date: Optional[str] = None,
    return_date: Optional[str] = None,
    travel_class: Optional[int] = None,
    multi_city_json: Optional[str] = None,
    show_hidden: Optional[bool] = None,
    deep_search: Optional[bool] = None,
    # Number of Passengers
    adults: Optional[int] = None,
    children: Optional[int] = None,
    infants_in_seat: Optional[int] = None,
    infants_on_lap: Optional[int] = None,
    # Sorting
    sort_by: Optional[int] = None,
    # Advanced Filters
    stops: Optional[int] = None,
    exclude_airlines: Optional[str] = None,
    include_airlines: Optional[str] = None,
    bags: Optional[int] = None,
    max_price: Optional[int] = None,
    outbound_times: Optional[str] = None,
    return_times: Optional[str] = None,
    emissions: Optional[int] = None,
    layover_duration: Optional[str] = None,
    exclude_conns: Optional[str] = None,
    max_duration: Optional[int] = None,
    # Next Flights
    departure_token: Optional[str] = None,
    # Booking Flights
    booking_token: Optional[str] = None,
    # SerpApi parameters
    no_cache: Optional[bool] = None,
    async_search: Optional[bool] = None,
    zero_trace: Optional[bool] = None,
    output: Optional[str] = None,
    json_restrictor: Optional[str] = None,
    # Legacy parameter for backward compatibility
    sort_by_price: Optional[bool] = None
) -> Dict[str, Any]:
    """
    Call the Google Flights API via SerpAPI to search for flights.
    Uses the official serpapi-python library.
    
    Args:
        # (All args are documented in the original function)
    
    Returns:
        Dict[str, Any]: API response containing flight data
    
    Raises:
        ValueError: If API key is not found
        Exception: If API request fails or returns an error
    """
    
    # Required parameters
    params = {
        "engine": "google_flights",
        # "api_key" is no longer needed here; it's set globally
    }
    
    # Add optional parameters only if they are not None
    optional_params = {
        # Search Query
        "departure_id": departure_id,
        "arrival_id": arrival_id,
        # Localization
        "gl": gl,
        "hl": hl,
        "currency": currency,
        # Advanced Google Flights Parameters
        "type": type,
        "outbound_date": outbound_date,
        "return_date": return_date,
        "travel_class": travel_class,
        "multi_city_json": multi_city_json,
        "show_hidden": show_hidden,
        "deep_search": deep_search,
        # Number of Passengers
        "adults": adults,
        "children": children,
        "infants_in_seat": infants_in_seat,
        "infants_on_lap": infants_on_lap,
        # Sorting
        "sort_by": sort_by,
        # Advanced Filters
        "stops": stops,
        "exclude_airlines": exclude_airlines,
        "include_airlines": include_airlines,
        "bags": bags,
        "max_price": max_price,
        "outbound_times": outbound_times,
        "return_times": return_times,
        "emissions": emissions,
        "layover_duration": layover_duration,
        "exclude_conns": exclude_conns,
        "max_duration": max_duration,
        # Next Flights
        "departure_token": departure_token,
        # Booking Flights
        "booking_token": booking_token,
        # SerpApi parameters
        "no_cache": no_cache,
        "async": async_search,
        "zero_trace": zero_trace,
        "output": output,
        "json_restrictor": json_restrictor
    }
    
    # Only add parameters that are not None
    for key, value in optional_params.items():
        if value is not None:
            params[key] = value
    
    # --- FIX: START ---
    # If a token is present, 'type' should be removed.
    # The API infers the type and other details from the token.
    if (departure_token is not None or booking_token is not None) and "type" in params:
        del params["type"]
    # --- FIX: END ---

    # Handle legacy sort_by_price parameter
    if sort_by_price is True and sort_by is None:
        params["sort_by"] = 2  # Sort by price
    
    try:
        # Use the GoogleSearch class to create and execute the search
        search = GoogleSearch(params)
        results = search.get_dict()
        
        # Check if the API returned an error in its response
        if "error" in results:
            raise Exception(results["error"])
        
        # Legacy support: Sort flights by price if sort_by_price was used
        # This logic should be handled by the API if sort_by=2 is set,
        # but we keep it for full backward compatibility with your original.
        if sort_by_price is True and "sort_by" not in params:
            if "best_flights" in results:
                results["best_flights"] = sorted(
                    results.get("best_flights", []), 
                    key=lambda x: float(x.get("price", 0))
                )
            if "other_flights" in results:
                results["other_flights"] = sorted(
                    results.get("other_flights", []), 
                    key=lambda x: float(x.get("price", 0))
                )
        
        return results
        
    except Exception as e:
        print(f"Error calling SerpAPI (Google Flights): {e}")
        raise

# Example of how you might call this function:
if __name__ == "__main__":
    try:
        # --- STEP 1: Search for Outbound Flights ---
        print("--- STEP 1: Searching for outbound flights... ---")
        flight_results = call_flights_api(
            departure_id="JFK",
            arrival_id="CDG",
            outbound_date="2025-12-01",  # Changed to a nearer date
            return_date="2025-12-08",  # Changed to a nearer date
            gl="us",
            hl="en",
            currency="USD",
            sort_by=2, # Sort by price
            stops=1    # Nonstop only
        )
        
        # Check for 'best_flights' first, if not, fall back to 'other_flights'
        best_flights = flight_results.get("best_flights")
        other_flights = flight_results.get("other_flights")
        all_flights = (best_flights or []) + (other_flights or [])
        
        if all_flights:
            top_flight = all_flights[0] 
            print(f"Found {len(all_flights)} outbound flights.")
            
            airline = "Unknown Airline"
            if top_flight.get('flights'):
                airline = top_flight['flights'][0].get('airline', 'Unknown Airline')

            print(f"Top outbound result: {airline} for ${top_flight.get('price')}")
            
            departure_token = top_flight.get('departure_token')
            
            if not departure_token:
                print("No 'departure_token' found for the top flight. Cannot proceed.")
                exit()
                
            # --- STEP 2: Get Return Flights using departure_token ---
            print(f"\n--- STEP 2: Getting return flights using token: {departure_token[:20]}... ---")
            return_flight_results = call_flights_api(
                departure_token=departure_token,
                departure_id="JFK",
                arrival_id="CDG",
                outbound_date="2025-12-01",  # Changed to a nearer date
                return_date="2025-12-08",  # Changed to a nearer date
                gl="us",
                hl="en",
                currency="USD",
                sort_by=2, # Sort by price
                stops=1    # Nonstop only
            )
            
            return_best_flights = return_flight_results.get("best_flights")
            return_other_flights = return_flight_results.get("other_flights")
            all_return_flights = (return_best_flights or []) + (return_other_flights or [])

            if all_return_flights:
                top_return_flight = all_return_flights[0]
                print(f"Found {len(all_return_flights)} return flights.")
                
                return_airline = "Unknown Airline"
                if top_return_flight.get('flights'):
                    return_airline = top_return_flight['flights'][0].get('airline', 'Unknown Airline')
                
                print(f"Top return result: {return_airline} for ${top_return_flight.get('price')}")

                booking_token = top_return_flight.get('booking_token')

                if not booking_token:
                    # Note: Sometimes the booking token is on the *outbound* flight in this step
                    booking_token = return_flight_results.get("best_flights", [{}])[0].get("booking_token") or \
                                    return_flight_results.get("other_flights", [{}])[0].get("booking_token")

                if not booking_token:
                    print("No 'booking_token' found for the return flight. Cannot proceed.")
                    exit()

                # --- STEP 3: Get Booking Links using booking_token ---
                print(f"\n--- STEP 3: Getting booking links using token: {booking_token[:20]}... ---")
                booking_results = call_flights_api(
                    booking_token=booking_token,
                    departure_id="JFK",
                    arrival_id="CDG",
                    outbound_date="2025-12-01",  # Changed to a nearer date
                    return_date="2025-12-08",  # Changed to a nearer date
                    gl="us",
                    hl="en",
                    currency="USD",
                    sort_by=2, # Sort by price
                    stops=1    # Nonstop only
                )

                if "booking_options" in booking_results and booking_results["booking_options"]:
                    print("\n--- SUCCESS! Found Booking Options: ---")
                    
                    # This is the single, reliable link you can send to your user.
                    # It leads to the Google Flights page with this exact trip selected.
                    google_link = booking_results.get("search_metadata", {}).get("google_flights_url")
                    if google_link:
                        print(f"\nHere is the Google Flights link to see all options:\n{google_link}")

                    # You can also iterate through the options and list them:
                    print("\n--- Booking Options Found: ---")
                    for option in booking_results["booking_options"]:
                        if "together" in option:
                            source = option["together"].get("book_with")
                            price = option["together"].get("price")
                            print(f"- Book with {source} for ${price}")
                            # Note: The 'booking_request' object inside the JSON is for a POST request,
                            # not a simple link. The 'google_flights_url' is the best link to use.
                
                else:
                    print("No booking options found in the final step.")
                # --- FIX: END ---
            
            else:
                print("No return flights found for the selected outbound flight.")
        
        else:
            print("No outbound flights found for this search.")

    except Exception as e:
        print(f"An error occurred: {e}")