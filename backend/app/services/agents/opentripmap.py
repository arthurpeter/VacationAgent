import asyncio
from typing import Optional, Sequence

import httpx

from app.core.config import settings
from app.core.logger import get_logger


OTM_BASE_URL = "https://api.opentripmap.com/0.1/en/places"
OTM_API_KEY = settings.OPENTRIPMAP_API_KEY
AUTOSUGGEST_RADIUS_METERS = 20000  # 20km radius in meters to catch landmark matches near city center.
KINDS_SEPARATOR = ","
CATEGORY_WORD_SEPARATOR = "_"
log = get_logger(__name__)


async def get_city_coordinates(city_name: str) -> Optional[dict]:
    if not city_name or not OTM_API_KEY:
        log.warning("OpenTripMap API key missing or city name empty.")
        return None

    url = f"{OTM_BASE_URL}/geoname"
    params = {"name": city_name, "apikey": OTM_API_KEY}

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params, timeout=10.0)
            if response.status_code != 200:
                log.warning("OpenTripMap geoname failed: %s", response.status_code)
                return None
            payload = response.json()
    except httpx.HTTPError as exc:
        log.warning("OpenTripMap geoname error: %s", exc)
        return None

    lat = payload.get("lat")
    lon = payload.get("lon")
    if lat is None or lon is None:
        return None

    return {"lat": lat, "lon": lon}


async def resolve_curated_places(
    place_names: Sequence[str],
    latitude: float,
    longitude: float
) -> list[dict]:
    if not place_names or not OTM_API_KEY:
        if not OTM_API_KEY:
            log.warning("OpenTripMap API key missing.")
        return []

    async with httpx.AsyncClient() as client:
        tasks = [
            _resolve_place(name, latitude, longitude, client)
            for name in place_names
            if name
        ]
        results = await asyncio.gather(*tasks)

    return [place for place in results if place]


async def _resolve_place(
    name: str,
    latitude: float,
    longitude: float,
    client: httpx.AsyncClient
) -> Optional[dict]:
    autosuggest_url = f"{OTM_BASE_URL}/autosuggest"
    params = {
        "name": name,
        "lat": latitude,
        "lon": longitude,
        "radius": AUTOSUGGEST_RADIUS_METERS,
        "limit": 1,
        "apikey": OTM_API_KEY
    }

    try:
        autosuggest_response = await client.get(autosuggest_url, params=params, timeout=10.0)
        if autosuggest_response.status_code != 200:
            return None
        suggestions = autosuggest_response.json()
    except httpx.HTTPError:
        return None

    if not suggestions:
        return None

    suggestion = suggestions[0]
    xid = suggestion.get("xid")
    if not xid:
        return None

    details_url = f"{OTM_BASE_URL}/xid/{xid}"
    try:
        details_response = await client.get(details_url, params={"apikey": OTM_API_KEY}, timeout=10.0)
        if details_response.status_code != 200:
            return None
        details = details_response.json()
    except httpx.HTTPError:
        return None

    point = details.get("point", {})
    preview = details.get("preview", {})
    wiki = details.get("wikipedia_extracts", {})
    kinds = details.get("kinds") or ""

    return {
        "external_place_id": xid,
        "name": details.get("name") or name,
        "category": _extract_category(kinds),
        "description": wiki.get("text") or details.get("info", {}).get("descr"),
        "image": preview.get("source"),
        "latitude": point.get("lat") or latitude,
        "longitude": point.get("lon") or longitude
    }


def _extract_category(kinds: str) -> Optional[str]:
    if not kinds:
        return None
    return kinds.split(KINDS_SEPARATOR)[0].replace(CATEGORY_WORD_SEPARATOR, " ")
