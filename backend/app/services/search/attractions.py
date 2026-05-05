import os
import httpx
import random
from typing import Dict, List, Optional
from app.core.logger import get_logger
from app.core.config import settings

log = get_logger(__name__)

OTM_BASE_URL = "https://api.opentripmap.com/0.1/en/places"


async def get_city_coordinates(city_name: str, country_code: Optional[str] = None) -> Optional[Dict[str, float]]:
    """1. Gets the exact center lat/lon of a city."""
    api_key = settings.OPENTRIPMAP_API_KEY
    if not api_key: return None

    async with httpx.AsyncClient() as client:
        try:
            params = {"name": city_name, "apikey": api_key}
            if country_code:
                params["country"] = country_code
            res = await client.get(
                f"{OTM_BASE_URL}/geoname",
                params=params
            )
            res.raise_for_status()
            data = res.json()
            if "lat" in data and "lon" in data:
                return {"lat": data["lat"], "lon": data["lon"], "name": data.get("name")}
            return None
        except httpx.HTTPError as e:
            log.error(f"OTM /geoname error for {city_name}: {str(e)}")
            return None


async def fetch_attractions_by_radius(lat: float, lon: float, radius: int = 15000, limit: int = 20) -> List[Dict]:
    """2. Finds top places using strict semantic filtering to avoid OSM noise."""
    api_key = settings.OPENTRIPMAP_API_KEY
    if not api_key: return []

    target_kinds = "museums,monuments_and_memorials,towers,historic_districts,palaces,castles"

    async with httpx.AsyncClient() as client:
        try:
            res = await client.get(
                f"{OTM_BASE_URL}/radius",
                params={
                    "radius": radius, 
                    "lon": lon, 
                    "lat": lat,
                    "kinds": target_kinds,
                    "rate": "3h",
                    "limit": 300,
                    "format": "json", 
                    "apikey": api_key
                }
            )
            res.raise_for_status()
            places = res.json()
            
            major_places = [p for p in places if p.get("osm", "").startswith(("way", "relation"))]
            
            if len(major_places) < limit:
                 major_places = places

            random.shuffle(major_places)
            
            sorted_places = sorted(major_places[:limit * 3], key=lambda x: -x.get("rate", 0))
            
            return sorted_places[:limit]
            
        except httpx.HTTPError as e:
            log.error(f"OTM /radius error: {str(e)}")
            return []


async def autosuggest_places(query: str, lat: float, lon: float, radius: int = 50000, limit: int = 5, min_rate: str = "3") -> List[Dict]:
    """3. Text search for specific places near the destination."""
    api_key = settings.OPENTRIPMAP_API_KEY
    if not api_key: return []

    async with httpx.AsyncClient() as client:
        try:
            res = await client.get(
                f"{OTM_BASE_URL}/autosuggest",
                params={
                    "name": query, "radius": radius, "lon": lon, "lat": lat,
                    "rate": min_rate,
                    "limit": 50,
                    "format": "json", "apikey": api_key
                }
            )
            res.raise_for_status()
            
            places = res.json()
            
            major_places = [p for p in places if p.get("osm", "").startswith(("way", "relation"))]
            if len(major_places) < limit:
                 major_places = places
                 
            sorted_places = sorted(major_places, key=lambda x: -x.get("rate", 0))
            return sorted_places[:limit]
            
        except httpx.HTTPError as e:
            log.error(f"OTM /autosuggest error for '{query}': {str(e)}")
            return []


async def get_place_details(xid: str) -> Optional[Dict]:
    """4. Deep dive on a specific place to get Images, Descriptions, and URLs."""
    api_key = settings.OPENTRIPMAP_API_KEY
    if not api_key: return None

    async with httpx.AsyncClient() as client:
        try:
            res = await client.get(f"{OTM_BASE_URL}/xid/{xid}", params={"apikey": api_key})
            res.raise_for_status()
            data = res.json()
            
            image_url = data.get("preview", {}).get("source")
            if image_url and "wikimedia.org" in image_url and "/thumb/" in image_url:
                parts = image_url.split("/")
                parts.pop()
                image_url = "/".join(parts).replace("/thumb/", "/")

            addr = data.get("address", {})
            street = addr.get("pedestrian") or addr.get("road") or ""
            house_num = addr.get("house_number", "")
            postcode = addr.get("postcode", "")
            city = addr.get("city", "")
            formatted_addr = f"{house_num} {street}, {postcode} {city}".strip(" ,")

            raw_rate = str(data.get("rate", "0"))
            clean_rate = float("".join(c for c in raw_rate if c.isdigit()) or 0)

            return {
                "external_place_id": data.get("xid"),
                "official_name": data.get("name"),
                "city": addr.get("city", ""),
                "state_province": addr.get("state", ""),
                "country": addr.get("country", ""),
                "formatted_address": formatted_addr if len(formatted_addr) > 5 else None,
                "latitude": data.get("point", {}).get("lat"),
                "longitude": data.get("point", {}).get("lon"),
                
                "image_url": image_url,
                "description": data.get("wikipedia_extracts", {}).get("text"),
                "website_url": data.get("url"),
                "rating": clean_rate,
                
                "tags": data.get("kinds", ""),
                "category": data.get("kinds", "").split(",")[0].replace("_", " ").title() if data.get("kinds") else "Attraction",
                "wikidata_id": data.get("wikidata")
            }
        except httpx.HTTPError as e:
            log.error(f"OTM /xid error for {xid}: {str(e)}")
            return None


if __name__ == "__main__":
    import asyncio
    import json

    async def run_tests():
        print("--- Testing 'Precision Search' Flow ---")
        
        if not settings.OPENTRIPMAP_API_KEY:
            print("❌ ERROR: OPENTRIPMAP_API_KEY is missing from your config!")
            return

        city = "Paris"
        print(f"\n[1] Fetching coordinates for '{city}'...")
        coords = await get_city_coordinates(city, "FR")
        
        if not coords:
            print("Stopping tests: Could not get coordinates.")
            return

        lat, lon = coords["lat"], coords["lon"]
        print(f"Result: {lat}, {lon}")

        query = "Eiffel Tower"
        print(f"\n[2] Autosuggest searching for '{query}'...")
        suggestions = await autosuggest_places(query, lat, lon, limit=10, min_rate="2")
        
        if not suggestions:
            print(f"No results found for '{query}'.")
            return

        print(f"Found {len(suggestions)} matches. Here are the top 5:")
        for i, s in enumerate(suggestions[:5]):
            osm_type = s.get("osm", "unknown").split("/")[0] if s.get("osm") else "unknown"
            print(f"  {i+1}. {s.get('name')} | Rate: {s.get('rate')} | OSM: {osm_type} | XID: {s.get('xid')}")

        top_match = suggestions[0]
        test_xid = top_match.get("xid")
        test_name = top_match.get("name")
        
        print(f"\n[3] Fetching deep details for the #1 match: '{test_name}' (XID: {test_xid})...")
        details = await get_place_details(test_xid)
        
        if details:
            print("\n--- THE FINAL DATABASE OBJECT ---")
            print(json.dumps(details, indent=2, ensure_ascii=False))
            print("---------------------------------")
            
            if details.get("description"):
                print("✅ Wikipedia Description Found!")
            else:
                print("❌ WARNING: No Description Found.")
                
            if details.get("image_url"):
                print("✅ Image URL Found!")
            else:
                print("❌ WARNING: No Image URL Found.")
        else:
            print("Failed to fetch details.")

    asyncio.run(run_tests())