import requests
import os
from typing import Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv()

def call_accomodation_api(
    query: str,
    check_in_date: str,
    check_out_date: str,
    adults: Optional[int] = None,
    children: Optional[int] = None,
    # Localization
    gl: Optional[str] = None,
    hl: Optional[str] = None,
    currency: Optional[str] = None,
    # Advanced parameters
    children_ages: Optional[str] = None,
    # Advanced filters
    sort_by: Optional[str] = None,
    min_price: Optional[int] = None,
    max_price: Optional[int] = None,
    property_types: Optional[str] = None,
    amenities: Optional[str] = None,
    rating: Optional[str] = None,
    # Hotels filters
    brands: Optional[str] = None,
    hotel_class: Optional[str] = None,
    free_cancellation: Optional[bool] = None,
    special_offers: Optional[bool] = None,
    eco_certified: Optional[bool] = None,
    # Vacation rentals filters
    vacation_rentals: Optional[bool] = None,
    bedrooms: Optional[int] = None,
    bathrooms: Optional[int] = None,
    # Pagination
    next_page_token: Optional[str] = None,
    # Property details
    property_token: Optional[str] = None,
    # SerpApi parameters
    no_cache: Optional[bool] = None,
    async_search: Optional[bool] = None,
    zero_trace: Optional[bool] = None,
    output: Optional[str] = None,
    json_restrictor: Optional[str] = None,
    # Legacy parameter for backward compatibility
    min_rating: Optional[float] = None
) -> Dict[str, Any]:
    """
    Call the Google Hotels API via SerpAPI to search for accommodations.
    
    Args:
        query (str): Search query (Required)
        check_in_date (str): Check-in date in YYYY-MM-DD format (Required)
        check_out_date (str): Check-out date in YYYY-MM-DD format (Required)
        adults (int, optional): Number of adults (default: 2 if not specified)
        children (int, optional): Number of children (default: 0 if not specified)
        
        # Localization
        gl (str, optional): Country code (e.g., "us", "uk", "fr")
        hl (str, optional): Language code (e.g., "en", "es", "fr")
        currency (str, optional): Currency code (e.g., "USD", "EUR", "GBP")
        
        # Advanced parameters
        children_ages (str, optional): Ages of children (e.g., "5" or "5,8,10")
        
        # Advanced filters
        sort_by (str, optional): Sort order - "3"=Lowest price, "8"=Highest rating, "13"=Most reviewed
        min_price (int, optional): Lower bound of price range
        max_price (int, optional): Upper bound of price range
        property_types (str, optional): Property types (e.g., "17" or "17,12,18")
        amenities (str, optional): Required amenities (e.g., "35" or "35,9,19")
        rating (str, optional): Minimum rating - "7"=3.5+, "8"=4.0+, "9"=4.5+
        
        # Hotels filters
        brands (str, optional): Hotel brands (e.g., "33" or "33,67,101")
        hotel_class (str, optional): Hotel class - "2"=2-star, "3"=3-star, "4"=4-star, "5"=5-star
        free_cancellation (bool, optional): Show only free cancellation options
        special_offers (bool, optional): Show only special offers
        eco_certified (bool, optional): Show only eco certified properties
        
        # Vacation rentals filters
        vacation_rentals (bool, optional): Search for vacation rentals instead of hotels
        bedrooms (int, optional): Minimum number of bedrooms
        bathrooms (int, optional): Minimum number of bathrooms
        
        # Pagination
        next_page_token (str, optional): Token for next page results
        
        # Property details
        property_token (str, optional): Token to get specific property details
        
        # SerpApi parameters
        no_cache (bool, optional): Force fresh results (not cached)
        async_search (bool, optional): Submit search asynchronously
        zero_trace (bool, optional): Enable ZeroTrace mode (Enterprise only)
        output (str, optional): Output format ("json" or "html")
        json_restrictor (str, optional): Restrict JSON response fields
        
        # Legacy parameter
        min_rating (float, optional): Minimum rating filter (legacy, use 'rating' instead)
    
    Returns:
        Dict[str, Any]: API response containing hotel data
    
    Raises:
        ValueError: If API key is not found or required parameters missing
        requests.RequestException: If API request fails
    """
    
    # Get API key from environment variable
    api_key = os.getenv('SERPAPI_API_KEY')
    if not api_key:
        raise ValueError("SERPAPI_API_KEY environment variable is required")
    
    # SerpAPI Google Hotels endpoint
    url = "https://serpapi.com/search"
    
    # Required parameters
    params = {
        "engine": "google_hotels",
        "q": query,
        "check_in_date": check_in_date,
        "check_out_date": check_out_date,
        "api_key": api_key
    }
    
    # Add optional parameters only if they are not None
    optional_params = {
        # Basic parameters
        "adults": adults,
        "children": children,
        # Localization
        "gl": gl,
        "hl": hl,
        "currency": currency,
        # Advanced parameters
        "children_ages": children_ages,
        # Advanced filters
        "sort_by": sort_by,
        "min_price": min_price,
        "max_price": max_price,
        "property_types": property_types,
        "amenities": amenities,
        "rating": rating,
        # Hotels filters
        "brands": brands,
        "hotel_class": hotel_class,
        "free_cancellation": free_cancellation,
        "special_offers": special_offers,
        "eco_certified": eco_certified,
        # Vacation rentals filters
        "vacation_rentals": vacation_rentals,
        "bedrooms": bedrooms,
        "bathrooms": bathrooms,
        # Pagination
        "next_page_token": next_page_token,
        # Property details
        "property_token": property_token,
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
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()  # Raises an HTTPError for bad responses
        
        data = response.json()
        
        # Apply minimum rating filter if specified
        if min_rating is not None and "properties" in data:
            filtered_properties = []
            for hotel in data["properties"]:
                rating = hotel.get("overall_rating")
                if rating is not None and rating >= min_rating:
                    filtered_properties.append(hotel)
            data["properties"] = filtered_properties
            # Update the count if it exists
            if "properties_count" in data:
                data["properties_count"] = len(filtered_properties)
        
        return data
        
    except requests.RequestException as e:
        print(f"Error calling SerpAPI: {e}")
        raise

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
    
    Args:
        # Search Query
        departure_id (str, optional): Departure airport code/kgmid (e.g., "JFK", "/m/04jpl")
        arrival_id (str, optional): Arrival airport code/kgmid (e.g., "CDG", "/m/04jpl")
        
        # Localization
        gl (str, optional): Country code (e.g., "us", "uk", "fr")
        hl (str, optional): Language code (e.g., "en", "es", "fr")
        currency (str, optional): Currency code (e.g., "USD", "EUR", "GBP")
        
        # Advanced Google Flights Parameters
        type (int, optional): Flight type - 1=Round trip, 2=One way, 3=Multi-city
        outbound_date (str, optional): Outbound date in YYYY-MM-DD format
        return_date (str, optional): Return date in YYYY-MM-DD format (required for round trip)
        travel_class (int, optional): 1=Economy, 2=Premium economy, 3=Business, 4=First
        multi_city_json (str, optional): JSON string for multi-city flights
        show_hidden (bool, optional): Include hidden flight results
        deep_search (bool, optional): Enable deep search for precise results
        
        # Number of Passengers
        adults (int, optional): Number of adults (default: 1)
        children (int, optional): Number of children (default: 0)
        infants_in_seat (int, optional): Number of infants in seat (default: 0)
        infants_on_lap (int, optional): Number of infants on lap (default: 0)
        
        # Sorting
        sort_by (int, optional): Sort order - 1=Top flights, 2=Price, 3=Departure time, 
                                4=Arrival time, 5=Duration, 6=Emissions
        
        # Advanced Filters
        stops (int, optional): Number of stops - 0=Any, 1=Nonstop, 2=1 stop or fewer, 3=2 stops or fewer
        exclude_airlines (str, optional): Airline codes to exclude (e.g., "UA,AA")
        include_airlines (str, optional): Airline codes to include (e.g., "UA,AA")
        bags (int, optional): Number of carry-on bags
        max_price (int, optional): Maximum ticket price
        outbound_times (str, optional): Outbound time range (e.g., "4,18" or "4,18,3,19")
        return_times (str, optional): Return time range (e.g., "4,18" or "4,18,3,19")
        emissions (int, optional): Emission level - 1=Less emissions only
        layover_duration (str, optional): Layover duration range in minutes (e.g., "90,330")
        exclude_conns (str, optional): Connecting airports to exclude (e.g., "CDG,AUS")
        max_duration (int, optional): Maximum flight duration in minutes
        
        # Next Flights
        departure_token (str, optional): Token to get returning flights
        
        # Booking Flights
        booking_token (str, optional): Token to get booking options
        
        # SerpApi parameters
        no_cache (bool, optional): Force fresh results (not cached)
        async_search (bool, optional): Submit search asynchronously
        zero_trace (bool, optional): Enable ZeroTrace mode (Enterprise only)
        output (str, optional): Output format ("json" or "html")
        json_restrictor (str, optional): Restrict JSON response fields
        
        # Legacy parameter
        sort_by_price (bool, optional): Legacy parameter (use 'sort_by=2' instead)
    
    Returns:
        Dict[str, Any]: API response containing flight data
    
    Raises:
        ValueError: If API key is not found
        requests.RequestException: If API request fails
    """
    
    # Get API key from environment variable
    api_key = os.getenv('SERPAPI_API_KEY')
    if not api_key:
        raise ValueError("SERPAPI_API_KEY environment variable is required")
    
    # SerpAPI Google Flights endpoint
    url = "https://serpapi.com/search"
    
    # Required parameters
    params = {
        "engine": "google_flights",
        "api_key": api_key
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
    
    # Handle legacy sort_by_price parameter
    if sort_by_price is True and sort_by is None:
        params["sort_by"] = 2  # Sort by price
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()  # Raises an HTTPError for bad responses
        
        data = response.json()
        
        # Legacy support: Sort flights by price if sort_by_price was used
        if sort_by_price is True and "sort_by" not in params:
            if "best_flights" in data:
                data["best_flights"] = sorted(
                    data["best_flights"], 
                    key=lambda x: float(x.get("price", 0))
                )
            if "other_flights" in data:
                data["other_flights"] = sorted(
                    data["other_flights"], 
                    key=lambda x: float(x.get("price", 0))
                )
        
        return data
        
    except requests.RequestException as e:
        print(f"Error calling SerpAPI: {e}")
        raise

# Example usage function
def example_hotel_search():
    """
    Example function showing how to use the enhanced call_accomodation_api function.
    """
    try:
        # Example 1: Basic hotel search with some filters
        print("=== Basic Hotel Search ===")
        results = call_accomodation_api(
            query="New York",
            check_in_date="2025-08-15",
            check_out_date="2025-08-17",
            adults=2,
            children=1,
            children_ages="8",
            gl="us",
            hl="en",
            currency="USD",
            sort_by="3",  # Lowest price
            rating="8",   # 4.0+ rating
            hotel_class="4,5",  # 4-5 star hotels
            free_cancellation=True
        )
        
        # Print basic info about found hotels
        if "properties" in results:
            print(f"Found {len(results['properties'])} hotels:")
            for hotel in results["properties"][:3]:  # Show first 3 hotels
                name = hotel.get("name", "Unknown")
                price = hotel.get("rate_per_night", {}).get("lowest", "N/A")
                rating = hotel.get("overall_rating", "N/A")
                print(f"- {name}: ${price}/night, Rating: {rating}")
        
        print("\n=== Vacation Rentals Search ===")
        # Example 2: Vacation rentals search
        vacation_results = call_accomodation_api(
            query="Miami Beach",
            check_in_date="2025-08-20",
            check_out_date="2025-08-25",
            adults=4,
            vacation_rentals=True,
            bedrooms=2,
            bathrooms=2,
            amenities="35,9",  # Pool and WiFi
            sort_by="3"  # Lowest price
        )
        
        if "properties" in vacation_results:
            print(f"Found {len(vacation_results['properties'])} vacation rentals:")
            for rental in vacation_results["properties"][:3]:
                name = rental.get("name", "Unknown")
                price = rental.get("rate_per_night", {}).get("lowest", "N/A")
                print(f"- {name}: ${price}/night")
        
    except Exception as e:
        print(f"Error in hotel search: {e}")

# Example usage function for flights
def example_flight_search():
    """
    Example function showing how to use the enhanced call_flights_api function.
    """
    try:
        # Example 1: Basic round trip flight search
        print("=== Round Trip Flight Search ===")
        results = call_flights_api(
            departure_id="JFK",
            arrival_id="CDG",
            type=1,  # Round trip
            outbound_date="2025-08-15",
            return_date="2025-08-22",
            adults=2,
            travel_class=1,  # Economy
            currency="USD",
            sort_by=2,  # Sort by price
            stops=1,  # Nonstop only
            deep_search=True  # More precise results
        )
        
        # Print basic info about found flights
        if "best_flights" in results:
            print(f"Found {len(results['best_flights'])} best flights:")
            for flight in results["best_flights"][:2]:  # Show first 2 flights
                for flight_info in flight.get("flights", []):
                    airline = flight_info.get("airline", "Unknown")
                    departure_time = flight_info.get("departure_airport", {}).get("time", "N/A")
                    arrival_time = flight_info.get("arrival_airport", {}).get("time", "N/A")
                    duration = flight_info.get("duration", "N/A")
                    print(f"- {airline}: {departure_time} → {arrival_time} ({duration})")
                price = flight.get("price", "N/A")
                print(f"  Price: {price}\n")
        
        print("=== One Way Flight with Filters ===")
        # Example 2: One way flight with advanced filters
        oneway_results = call_flights_api(
            departure_id="LAX",
            arrival_id="NRT",
            type=2,  # One way
            outbound_date="2025-09-01",
            adults=1,
            travel_class=3,  # Business class
            include_airlines="AA,JL",  # American Airlines and JAL only
            outbound_times="8,18",  # Departure between 8 AM and 6 PM
            max_duration=720,  # Max 12 hours
            emissions=1,  # Less emissions only
            sort_by=5  # Sort by duration
        )
        
        if "best_flights" in oneway_results:
            print(f"Found {len(oneway_results['best_flights'])} business class flights:")
            for flight in oneway_results["best_flights"][:2]:
                for flight_info in flight.get("flights", []):
                    airline = flight_info.get("airline", "Unknown")
                    duration = flight_info.get("duration", "N/A")
                    print(f"- {airline}: {duration}")
                price = flight.get("price", "N/A")
                print(f"  Price: {price}\n")
        
        print("=== Multi-City Flight ===")
        # Example 3: Multi-city flight
        multi_city_json = '[{"departure_id":"NYC","arrival_id":"PAR","date":"2025-10-01"},{"departure_id":"PAR","arrival_id":"TOK","date":"2025-10-08"},{"departure_id":"TOK","arrival_id":"NYC","date":"2025-10-15"}]'
        
        multi_results = call_flights_api(
            type=3,  # Multi-city
            multi_city_json=multi_city_json,
            adults=1,
            travel_class=1,  # Economy
            sort_by=2  # Sort by price
        )
        
        if "best_flights" in multi_results:
            print(f"Found {len(multi_results['best_flights'])} multi-city itineraries")
            
    except Exception as e:
        print(f"Error in flight search: {e}")

if __name__ == "__main__":
    # Uncomment the lines below to test the functions
    # example_hotel_search()
    # example_flight_search()
    pass