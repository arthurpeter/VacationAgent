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
    Uses the official serpapi-python library.
    
    Args:
        query (str): Search query (Required)
        check_in_date (str): Check-in date in YYYY-MM-DD format (Required)
        check_out_date (str): Check-out date in YYYY-MM-DD format (Required)
        # (All other args are documented in the original function)
    
    Returns:
        Dict[str, Any]: API response containing hotel data
    
    Raises:
        ValueError: If required parameters are missing
        Exception: If API request fails or returns an error
    """
    
    # Required parameters
    params = {
        "engine": "google_hotels",
        "q": query,
        "check_in_date": check_in_date,
        "check_out_date": check_out_date,
        # "api_key" is no longer needed here; it's set globally
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
        "async": async_search,  # Note: The library expects 'async'
        "zero_trace": zero_trace,
        "output": output,
        "json_restrictor": json_restrictor
    }
    
    # Only add parameters that are not None
    for key, value in optional_params.items():
        if value is not None:
            params[key] = value
    
    try:
        # Use the GoogleSearch class to create and execute the search
        search = GoogleSearch(params)
        results = search.get_dict()
        
        # Check if the API returned an error in its response
        if "error" in results:
            raise Exception(results["error"])
        
        # Apply minimum rating filter if specified (legacy logic)
        if min_rating is not None and "properties" in results:
            filtered_properties = []
            for hotel in results.get("properties", []):
                hotel_rating = hotel.get("overall_rating")
                if hotel_rating is not None and hotel_rating >= min_rating:
                    filtered_properties.append(hotel)
            results["properties"] = filtered_properties
            # Update the count if it exists
            if "properties_count" in results:
                results["properties_count"] = len(filtered_properties)
        
        return results
        
    except Exception as e:
        print(f"Error calling SerpAPI (Google Hotels): {e}")
        raise

# Example of how you might call this function:
if __name__ == "__main__":
    try:
        hotel_results = call_accomodation_api(
            query="Hotels in Paris, France",
            check_in_date="2025-12-10",
            check_out_date="2025-12-17",
            gl="us",
            hl="en",
            currency="USD",
            rating="8"  # 4.0+ stars
        )
        
        if "properties" in hotel_results and hotel_results["properties"]:
            print(f"Found {len(hotel_results['properties'])} hotels.")
            print(f"Top result: {hotel_results['properties'][0].get('name')}")
            print(f"Price: {hotel_results['properties'][0].get('price')}")
        else:
            print("No properties found for this search.")

    except Exception as e:
        print(f"An error occurred: {e}")