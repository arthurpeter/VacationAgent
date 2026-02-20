import os
from serpapi import GoogleSearch  # Import the official library
from typing import Dict, Any, Optional
from dotenv import load_dotenv
import airportsdata
from babel import numbers, core
import sys
from app.core.cache import redis_cache

load_dotenv()

@redis_cache(expire_time=3600 * 24 * 7)
def get_location_data(area_input: str, country_filter: str = None):
    """
    Takes an area (City Name OR Airport Code) and returns all necessary
    search parameters in one go.
    
    Args:
        area_input: "Paris", "London", "OTP", or "LON"
        country_filter: Optional "FR", "GB" (useful if searching 'Paris, US' vs 'Paris, FR')
        
    Returns:
        dict: {
            "airport_list": "CDG,ORY,LBG",  # The code(s) for the search
            "gl": "fr",                     # Country parameter
            "hl": "en",                     # Language parameter
            "currency": "EUR"               # Currency parameter
        }
    """
    airports = airportsdata.load('IATA')
    area_clean = area_input.strip()

    found_airports = []
    
    target_city = area_clean.lower()
    target_code = area_clean.upper()
    target_country = country_filter.strip().upper() if country_filter else None

    for code, data in airports.items():
        is_city_match = (data.get('city', '').lower() == target_city)
        is_code_match = (code == target_code)
        
        if is_city_match or is_code_match:
            if target_country and data.get('country') != target_country:
                continue
                
            if len(code) == 3:
                found_airports.append(data)

    if not found_airports:
        return {"error": f"No airports found for '{area_input}'"}

    first_match = found_airports[0]
    country_code = first_match['country']
    
    currency_list = numbers.get_territory_currencies(country_code)
    currency_code = currency_list[0] if currency_list else "USD"
    
    codes_str = ",".join(list(set([a['iata'] for a in found_airports])))

    return {
        "departure_id": codes_str,
        "gl": country_code.lower(),
        "hl": "en",
        "currency": currency_code.upper()
    }

GoogleSearch.SERP_API_KEY = os.getenv('SERPAPI_API_KEY')
if not GoogleSearch.SERP_API_KEY:
    raise ValueError("SERPAPI_API_KEY environment variable is required")

# change to 3 - 15 minutes in prod
@redis_cache(expire_time=3600 * 24)
def call_flights_api(
    departure_id: Optional[str] = None,
    arrival_id: Optional[str] = None,
    gl: Optional[str] = None,
    hl: Optional[str] = None,
    currency: Optional[str] = None,
    type: Optional[int] = 1,
    outbound_date: Optional[str] = None,
    return_date: Optional[str] = None,
    travel_class: Optional[int] = None,
    multi_city_json: Optional[str] = None,
    show_hidden: Optional[bool] = None,
    deep_search: Optional[bool] = None,
    adults: Optional[int] = None,
    children: Optional[int] = None,
    infants_in_seat: Optional[int] = None,
    infants_on_lap: Optional[int] = None,
    sort_by: Optional[int] = None,
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
    departure_token: Optional[str] = None,
    booking_token: Optional[str] = None,
    no_cache: Optional[bool] = None,
    async_search: Optional[bool] = None,
    zero_trace: Optional[bool] = None,
    output: Optional[str] = None,
    json_restrictor: Optional[str] = None,
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
    
    params = {
        "engine": "google_flights",
    }
    
    optional_params = {
        "departure_id": departure_id,
        "arrival_id": arrival_id,
        "gl": gl,
        "hl": hl,
        "currency": currency,
        "type": type,
        "outbound_date": outbound_date,
        "return_date": return_date,
        "travel_class": travel_class,
        "multi_city_json": multi_city_json,
        "show_hidden": show_hidden,
        "deep_search": deep_search,
        "adults": adults,
        "children": children,
        "infants_in_seat": infants_in_seat,
        "infants_on_lap": infants_on_lap,
        "sort_by": sort_by,
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
        "departure_token": departure_token,
        "booking_token": booking_token,
        "no_cache": no_cache,
        "async": async_search,
        "zero_trace": zero_trace,
        "output": output,
        "json_restrictor": json_restrictor
    }
    
    for key, value in optional_params.items():
        if value is not None:
            params[key] = value
    
    if (departure_token is not None or booking_token is not None) and "type" in params:
        del params["type"]

    if sort_by_price is True and sort_by is None:
        params["sort_by"] = 2
    
    try:
        search = GoogleSearch(params)
        results = search.get_dict()
        
        if "error" in results:
            raise Exception(results["error"])
        
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

if __name__ == "__main__":
    print(get_location_data("Rome", "IT"))
    sys.exit()
    try:
        print("--- STEP 1: Searching for outbound flights... ---")
        flight_results = call_flights_api(
            departure_id="JFK",
            arrival_id="CDG",
            outbound_date="2026-08-01",
            return_date="2026-08-08",
            gl="us",
            hl="en",
            currency="USD",
            sort_by=2,
            stops=1
        )
        
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
                
            print(f"\n--- STEP 2: Getting return flights using token: {departure_token[:20]}... ---")
            return_flight_results = call_flights_api(
                departure_token=departure_token,
                departure_id="JFK",
                arrival_id="CDG",
                outbound_date="2026-08-01",
                return_date="2026-08-08",
                gl="us",
                hl="en",
                currency="USD",
                sort_by=2,
                stops=1
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
                    booking_token = return_flight_results.get("best_flights", [{}])[0].get("booking_token") or \
                                    return_flight_results.get("other_flights", [{}])[0].get("booking_token")

                if not booking_token:
                    print("No 'booking_token' found for the return flight. Cannot proceed.")
                    exit()

                print(f"\n--- STEP 3: Getting booking links using token: {booking_token[:20]}... ---")
                booking_results = call_flights_api(
                    booking_token=booking_token,
                    departure_id="JFK",
                    arrival_id="CDG",
                    outbound_date="2026-08-01",
                    return_date="2026-08-08",
                    gl="us",
                    hl="en",
                    currency="USD",
                    sort_by=2,
                    stops=1
                )

                if "booking_options" in booking_results and booking_results["booking_options"]:
                    print("\n--- SUCCESS! Found Booking Options: ---")
                    
                    google_link = booking_results.get("search_metadata", {}).get("google_flights_url")
                    if google_link:
                        print(f"\nHere is the Google Flights link to see all options:\n{google_link}")

                    print("\n--- Booking Options Found: ---")
                    for option in booking_results["booking_options"]:
                        if "together" in option:
                            source = option["together"].get("book_with")
                            price = option["together"].get("price")
                            print(f"- Book with {source} for ${price}")
                
                else:
                    print("No booking options found in the final step.") 
            else:
                print("No return flights found for the selected outbound flight.")
        
        else:
            print("No outbound flights found for this search.")

    except Exception as e:
        print(f"An error occurred: {e}")