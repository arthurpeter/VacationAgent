from serpapi import GoogleSearch
from typing import Dict, Any, Optional
from app.core.config import settings


GoogleSearch.SERP_API_KEY = settings.SERPAPI_API_KEY
if not GoogleSearch.SERP_API_KEY:
    raise ValueError("SERPAPI_API_KEY environment variable is required")


def call_accommodation_api(
    query: str,
    check_in_date: str,
    check_out_date: str,
    adults: Optional[int] = None,
    children: Optional[int] = None,
    gl: Optional[str] = None,
    hl: Optional[str] = None,
    currency: Optional[str] = None,
    children_ages: Optional[str] = None,
    sort_by: Optional[str] = None,
    min_price: Optional[int] = None,
    max_price: Optional[int] = None,
    property_types: Optional[str] = None,
    amenities: Optional[str] = None,
    rating: Optional[str] = None,
    brands: Optional[str] = None,
    hotel_class: Optional[str] = None,
    free_cancellation: Optional[bool] = None,
    special_offers: Optional[bool] = None,
    eco_certified: Optional[bool] = None,
    vacation_rentals: Optional[bool] = None,
    bedrooms: Optional[int] = None,
    bathrooms: Optional[int] = None,
    next_page_token: Optional[str] = None,
    property_token: Optional[str] = None,
    no_cache: Optional[bool] = None,
    async_search: Optional[bool] = None,
    zero_trace: Optional[bool] = None,
    output: Optional[str] = None,
    json_restrictor: Optional[str] = None,
    min_rating: Optional[float] = None,
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
        Exception: If API request fails or returns an error
    """

    params = {
        "engine": "google_hotels",
        "q": query,
        "check_in_date": check_in_date,
        "check_out_date": check_out_date,
    }

    optional_params = {
        "adults": adults,
        "children": children,
        "gl": gl,
        "hl": hl,
        "currency": currency,
        "children_ages": children_ages,
        "sort_by": sort_by,
        "min_price": min_price,
        "max_price": max_price,
        "property_types": property_types,
        "amenities": amenities,
        "rating": rating,
        "brands": brands,
        "hotel_class": hotel_class,
        "free_cancellation": free_cancellation,
        "special_offers": special_offers,
        "eco_certified": eco_certified,
        "vacation_rentals": vacation_rentals,
        "bedrooms": bedrooms,
        "bathrooms": bathrooms,
        "next_page_token": next_page_token,
        "property_token": property_token,
        "no_cache": no_cache,
        "async": async_search,
        "zero_trace": zero_trace,
        "output": output,
        "json_restrictor": json_restrictor,
    }

    for key, value in optional_params.items():
        if value is not None:
            params[key] = value

    try:
        search = GoogleSearch(params)
        results = search.get_dict()

        if "error" in results:
            raise Exception(results["error"])

        if min_rating is not None and "properties" in results:
            filtered_properties = []
            for hotel in results.get("properties", []):
                hotel_rating = hotel.get("overall_rating")
                if hotel_rating is not None and hotel_rating >= min_rating:
                    filtered_properties.append(hotel)
            results["properties"] = filtered_properties

            if "properties_count" in results:
                results["properties_count"] = len(filtered_properties)

        return results

    except Exception as e:
        print(f"Error calling SerpAPI (Google Hotels): {e}")
        raise


if __name__ == "__main__":
    try:
        search_query = "Hotels in Paris, France"

        ci_date = "2026-02-10"
        co_date = "2026-02-17"

        print("--- STEP 1: Searching for hotels and links... ---")
        hotel_results = call_accommodation_api(
            query=search_query,
            check_in_date=ci_date,
            check_out_date=co_date,
            gl="us",
            hl="en",
            currency="USD",
            rating="8",
            sort_by="3",
        )

        print("\n--- ✅ Found Sponsored Provider Link ---")
        ads = hotel_results.get("ads")
        if ads:
            first_ad = ads[0]
            print(f"Provider: {first_ad.get('source')}")
            print(f"Name: {first_ad.get('name')}")
            print(f"Price: {first_ad.get('price')}")
            print(f"Link: {first_ad.get('link')}")
        else:
            print("No sponsored (ad) results found.")

        print("\n--- ✅ Found Top Organic Property Link ---")
        if "properties" in hotel_results and hotel_results["properties"]:
            properties = hotel_results["properties"]

            top_hotel = None
            for hotel in properties:
                if hotel.get("total_rate") and hotel.get("total_rate").get("lowest"):
                    top_hotel = hotel
                    break

            if top_hotel is None:
                print(
                    "Warning: No hotels in the list had a 'total_rate'. Falling back to first result."
                )
                top_hotel = properties[0]

            hotel_price = top_hotel.get("total_rate", {}).get("lowest")
            if not hotel_price:
                hotel_price = top_hotel.get("price")

            print(f"Name: {top_hotel.get('name')}")
            print(f"Total Price: {hotel_price}")

            property_link = top_hotel.get("link")
            if property_link:
                print(f"Link: {property_link}")
            else:
                print(
                    "Link: (This property has no direct provider link, only a 'property_token')"
                )

        else:
            print("No properties found for this search.")

    except Exception as e:
        print(f"An error occurred: {e}")
