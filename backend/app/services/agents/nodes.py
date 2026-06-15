import asyncio
from typing import Literal

import orjson
import json
import anyio

from app.services.agents.memory import DiscoveryState, ItineraryState
from app.services.agents.prompts import *
from langgraph.store.base import BaseStore
from langgraph.graph import END
from langgraph.types import Overwrite

from app.services.agents.responses import *
from app.core.config import settings

from datetime import datetime
from sqlalchemy import update, select
from app.core.database import SessionLocal
from app.models.vacation_session import VacationSession
from app.services.agents.utils import is_llm_null, resolve_location, get_resumed_state
from langchain_core.messages import HumanMessage, RemoveMessage, SystemMessage
from app.services.agents.tools import responder_tools, link_finder_tools, detailer_tools, web_search_tool
from app.core.logger import get_logger
from app.models.global_attraction import GlobalAttraction
from app.services.search.attractions import *
from timezonefinder import TimezoneFinder
from langchain_tavily import TavilySearch

from app.services.agents.mobility_strategies import MobilityConfig
from app.services.scheduling.engine import ScheduleEngine
from app.services.scheduling.maps import get_transit_bundle_for_leg

log = get_logger(__name__)


llm = settings.llm

# Discovery Graph Nodes

async def information_collector(state: DiscoveryState) -> dict:
    """
    Node 1: Parses the user's message and extracts new trip parameters 
    into a transient buffer.
    """
    current_knowledge = "\n".join([
        f"- {k}: {v}" for k, v in state.get("extracted_data", {}).items() if v is not None
    ]) if state.get("extracted_data") else "No information collected yet."

    today_str = datetime.now().strftime("%A, %B %d, %Y")

    messages = state.get("messages", [])
    recent_msgs = messages[-2:] if len(messages) >= 2 else messages
    chat_context = ""
    for msg in recent_msgs:
        role = "User" if msg.type == "human" else "Assistant"
        chat_context += f"{role}: {msg.content}\n"

    instructions = information_collector_prompt.format(
        current_date=today_str,
        persona=state.get("persona_context", "None"),
        current_knowledge=current_knowledge,
        recent_chat_history=chat_context.strip()
    )

    structured_llm = llm.with_structured_output(ExtractionResult)
    response = await structured_llm.ainvoke(instructions)
    return {"newly_extracted_data": response.model_dump()}


async def db_validator(state: DiscoveryState) -> dict:
    """
    Node 2: Validates the extracted trip parameters and adds them to the database.
    """
    new_info = state.get("newly_extracted_data") or {}
    session_id = state.get("session_id")
    user_id = state.get("user_id")

    passengers_confirmed = state.get("passengers_confirmed", False)
    if new_info.get("passengers_confirmed") is True:
        passengers_confirmed = True

    if new_info:
        update_values = {}
        for k, v in new_info.items():
            if is_llm_null(v) or k == "is_change_request" or k == "passengers_confirmed": continue
            
            if k in ["departure", "destination"]:
                if not v or len(v) < 3: continue
                v = await resolve_location(str(v))
            
            if k in ["from_date", "to_date"] and isinstance(v, str):
                try:
                    v = datetime.strptime(v, "%Y-%m-%d")
                except ValueError: continue
            
            update_values[k] = v

        async with SessionLocal() as db:
            if update_values:
                await db.execute(
                    update(VacationSession)
                    .where(VacationSession.id == session_id, VacationSession.user_id == user_id)
                    .values(**update_values)
                )
                await db.commit()

            refreshed_data = await get_resumed_state(db, session_id)

    is_valid = False
    mandatory = ["departure", "destination", "from_date", "to_date", "adults", "currency", "room_qty"]
    
    if all(refreshed_data.get(f) for f in mandatory):
        d1 = datetime.fromisoformat(refreshed_data["from_date"]).replace(tzinfo=None)
        d2 = datetime.fromisoformat(refreshed_data["to_date"]).replace(tzinfo=None)
        
        basic_logic = (
            d1 < d2 and 
            d1 > datetime.now() and 
            refreshed_data["departure"] != refreshed_data["destination"] and
            (refreshed_data["adults"] or 0) >= 1
        )

        ages_str = refreshed_data.get("children_ages") or ""
        ages_list = [int(a.strip()) for a in ages_str.split(",") if a.strip().isdigit()]
        
        infants_from_ages = len([a for a in ages_list if a < 2])
        children_from_ages = len([a for a in ages_list if 2 <= a < 18])
        
        infant_total_count = (refreshed_data.get("infants_in_seat") or 0) + (refreshed_data.get("infants_on_lap") or 0)
        child_total_count = refreshed_data.get("children") or 0

        consistency_ok = (infants_from_ages == infant_total_count and children_from_ages == child_total_count)

        if basic_logic and consistency_ok:
            is_valid = True

    return {
        "extracted_data": refreshed_data,
        "is_complete": is_valid,
        "passengers_confirmed": passengers_confirmed
    }

async def responder(state: DiscoveryState) -> dict:
    """
    Node 3: Formulates the final response to the user and can call tools.
    """
    is_complete = state.get("is_complete", False)
    current_data = state.get("extracted_data", {})
    all_messages = state.get("messages", [])
    
    persona = state.get("persona", "Unknown traveler.")
    passengers_confirmed = state.get("passengers_confirmed", False)
    
    required_keys = ["origin", "destination", "from_date", "to_date", "adults"]
    missing_fields = [k for k in required_keys if not current_data.get(k)]

    last_human_idx = -1
    for i in range(len(all_messages) - 1, -1, -1):
        if all_messages[i].type == "human":
            last_human_idx = i
            break

    if last_human_idx != -1:
        start_idx = max(0, last_human_idx - 10)
        older_messages = all_messages[start_idx:last_human_idx]
        current_messages = all_messages[last_human_idx:]
    else:
        older_messages = []
        current_messages = all_messages

    history_str = ""
    for msg in older_messages:
        if msg.type == "human":
            history_str += f"Human: {msg.content}\n"
        elif msg.type == "ai":
            if hasattr(msg, "tool_calls") and msg.tool_calls:
                tools_used = ", ".join([tc["name"] for tc in msg.tool_calls])
                history_str += f"Assistant (Action): Used tool [{tools_used}]\n"
            elif msg.content:
                history_str += f"Assistant: {msg.content}\n"
        elif msg.type == "tool":
            content_str = str(msg.content)
            short_content = content_str if len(content_str) < 300 else content_str[:300] + "..."
            history_str += f"Tool Result ({msg.name}): {short_content}\n"
            
    if not history_str:
        history_str = "No previous conversation history."

    user_history_str = state.get("user_history", "No prior travel history recorded with us.")
    
    system_instructions = responder_prompt.format(
        persona=persona,
        user_history=user_history_str,
        current_data=current_data,
        missing_fields=missing_fields,
        is_complete=is_complete,
        passengers_confirmed=passengers_confirmed,
        history=history_str
    )

    llm_with_tools = llm.bind_tools(responder_tools)
    
    response = await llm_with_tools.ainvoke([SystemMessage(content=system_instructions)] + current_messages)
    
    return {"messages": [response]}


# Itinerary Graph Nodes

search_tool = TavilySearch(max_results=5, tavily_api_key=settings.TAVILY_API_KEY)

async def picking_attractions(state: ItineraryState) -> dict:
    action = state.get("action")
    
    destination = state.get("search_location", "").split(",")
    if len(destination) < 2:
        log.error("Invalid destination format in state['search_location']")
        return {}
        
    city = destination[0].strip()
    country = destination[1].strip()

    updates = {
        "resolved_attractions": Overwrite([]),
        "unresolved_attractions": [],
        "action": "idle"
    }

    def format_cached_poi(p):
        return {
            "external_place_id": p.external_place_id,
            "wikidata_id": p.wikidata_id,
            "official_name": p.official_name,
            "city": p.city,
            "state_province": p.state_province,
            "country": p.country,
            "formatted_address": p.formatted_address,
            "timezone": p.timezone,
            "latitude": p.latitude,
            "longitude": p.longitude,
            "category": p.category,
            "tags": p.tags,
            "description": p.description,
            "image_url": p.image_url,
            "website_url": p.website_url,
            "rating": p.rating,
            "price_tier": p.price_tier,
            "recommended_duration_mins": p.recommended_duration_mins,
            "tod_preference": p.tod_preference,
            "id": p.id,
            "opening_hours": p.opening_hours,
            "needs_reservation": p.needs_reservation
        }

    if action == "initial_fetch":
        log.info(f"Starting Initial Fetch for {city}, {country}...")
        
        async with SessionLocal() as db:
            stmt = select(GlobalAttraction).where(
                GlobalAttraction.city.ilike(f"%{city}%") & 
                GlobalAttraction.country.ilike(f"%{country}%")
            ).order_by(GlobalAttraction.dynamic_relevance_rank().desc()).limit(20)
            result = await db.execute(stmt)
            existing_places = result.scalars().all()

            if len(existing_places) >= 10:
                log.info(f"CACHE HIT: Showing {len(existing_places)} existing places from DB.")

                hit_ids = [p.id for p in existing_places]
                await GlobalAttraction.track_search_metrics(db, hit_ids)

                updates["resolved_attractions"] = Overwrite([format_cached_poi(p) for p in existing_places])
                return updates

            coords = await get_city_coordinates(city, country)
            if not coords: return updates

            structured_llm = llm.with_structured_output(AttractionList)
            prompt = attraction_picker_prompt.format(
                persona=state.get("persona", "Traveler"),
                destination=f"{city}, {country}",
            )

            response = await structured_llm.ainvoke(prompt)
            attraction_names = response.attractions

            db_hits = []
            new_finds = []
            loop_hit_ids = []

            for name in attraction_names:
                poi_data = await autosuggest_places(name, coords["lat"], coords["lon"], limit=1)
                if not poi_data: continue
                
                xid = poi_data[0]["xid"]
                stmt = select(GlobalAttraction).where(GlobalAttraction.external_place_id == xid)
                res = await db.execute(stmt)
                cached = res.scalars().first()

                if cached:
                    db_hits.append(format_cached_poi(cached))
                    loop_hit_ids.append(cached.id)
                else:
                    resolved = await get_place_details(xid)
                    if resolved:
                        resolved["city"] = city
                        resolved["country"] = country 
                        new_finds.append(resolved)
                
                await asyncio.sleep(0.5)

            if loop_hit_ids:
                await GlobalAttraction.track_search_metrics(db, loop_hit_ids)

            updates.update({
                "unresolved_attractions": new_finds,
                "resolved_attractions": Overwrite(db_hits),
                "action": "resolve_attractions" if new_finds else "idle"
            })

    elif action == "custom_search":
        log.info(f"Executing Custom Search for {city}, {country}...")

        messages = state.get("messages", [])
        user_query = "Interesting places"
        if messages:
            last_message = messages[-1]
            user_query = last_message.content if hasattr(last_message, "content") else last_message.get("content", str(last_message))

        coords = await get_city_coordinates(city, country)
        if not coords: return updates

        structured_llm = llm.with_structured_output(AttractionList)
        prompt = custom_search_prompt.format(
            destination=f"{city}, {country}",
            user_query=user_query
        )
        
        response = await structured_llm.ainvoke(prompt)
        attraction_names = response.attractions

        db_hits = []
        new_finds = []
        custom_hit_ids = []

        async with SessionLocal() as db:
            for name in attraction_names:
                poi_data = await autosuggest_places(name, coords["lat"], coords["lon"], limit=1)
                if not poi_data: continue
                
                xid = poi_data[0]["xid"]
                stmt = select(GlobalAttraction).where(GlobalAttraction.external_place_id == xid)
                res = await db.execute(stmt)
                cached = res.scalars().first()

                if cached:
                    log.info(f"SMART CACHE HIT: {name} found in DB.")
                    db_hits.append(format_cached_poi(cached))
                    custom_hit_ids.append(cached.id)
                else:
                    log.info(f"NEW ATTRACTION: {name} not in DB, fetching OTM details...")
                    resolved = await get_place_details(xid)
                    if resolved:
                        resolved["city"] = city
                        resolved["country"] = country 
                        new_finds.append(resolved)
                
                await asyncio.sleep(0.5)

            if custom_hit_ids:
                await GlobalAttraction.track_search_metrics(db, custom_hit_ids)

        updates.update({
            "unresolved_attractions": new_finds,
            "resolved_attractions": Overwrite(db_hits),
            "action": "resolve_attractions" if new_finds else "idle"
        })

    log.info(updates)       
    return updates
    
async def enrich_single_attraction_node(poi_data: dict) -> dict:
    name = poi_data.get("official_name", "Unknown Place")
    otm_city = poi_data.get("city", "Unknown City")
    otm_country = poi_data.get("country", "Unknown")
    otm_description = poi_data.get("description", "No description available.")
    
    search_query = (
        f"{name} in {otm_city} {otm_country} official website, "
        f"opening hours for each day of the week, "
        f"ticket price, recommended duration, rating"
    )
    search_results = await search_tool.ainvoke({"query": search_query})
    
    if isinstance(search_results, str):
        context_text = search_results
    elif isinstance(search_results, list):
        if len(search_results) > 0 and isinstance(search_results[0], dict):
            context_text = "\n".join([res.get("content", "") for res in search_results])
        else:
            context_text = "\n".join(str(res) for res in search_results)
    else:
        context_text = str(search_results)

    structured_llm = llm.with_structured_output(AttractionEnrichmentSchema)
    prompt = extraction_prompt.format(
        name=name,
        otm_city=otm_city,
        otm_country=otm_country,
        otm_description=otm_description,
        context=context_text
    )

    extracted_data = await structured_llm.ainvoke(prompt)

    lat = poi_data.get("latitude")
    lon = poi_data.get("longitude")
    tf = TimezoneFinder()
    tz_string = tf.timezone_at(lat=lat, lng=lon) if lat and lon else None

    raw_hours = extracted_data.opening_hours.model_dump()
    clean_hours = {day: (val if val and val.strip() else "N/A") for day, val in raw_hours.items()}

    enriched_poi = {
        **poi_data,
        "price_tier": extracted_data.price_tier,
        "recommended_duration_mins": extracted_data.recommended_duration_mins,
        "tod_preference": extracted_data.tod_preference,
        "timezone": tz_string,
        "rating": extracted_data.rating,
        "description": extracted_data.description,
        "website_url": extracted_data.website_url or poi_data.get("website_url"),
        "city": extracted_data.city,
        "country": extracted_data.country,
        "opening_hours": clean_hours,
        "needs_reservation": extracted_data.needs_reservation
    }

    return {"resolved_attractions": [enriched_poi]}

async def save_attractions_to_db(state: ItineraryState) -> dict:
    resolved = state.get("resolved_attractions", [])
    if not resolved:
        return {"action": "move_to_next_stage"}

    updated_resolved_list = []
    
    async with SessionLocal() as db:
        for poi_data in resolved:
            stmt = select(GlobalAttraction).where(GlobalAttraction.external_place_id == poi_data.get("external_place_id"))
            result = await db.execute(stmt)
            existing_place = result.scalars().first()
            
            if not existing_place:
                new_attraction = GlobalAttraction(
                    external_place_id=poi_data.get("external_place_id"),
                    wikidata_id=poi_data.get("wikidata_id"),
                    official_name=poi_data.get("official_name"),
                    city=poi_data.get("city"),
                    state_province=poi_data.get("state_province"),
                    country=poi_data.get("country"),
                    formatted_address=poi_data.get("formatted_address"),
                    timezone=poi_data.get("timezone"),
                    latitude=poi_data.get("latitude"),
                    longitude=poi_data.get("longitude"),
                    category=poi_data.get("category"),
                    tags=poi_data.get("tags"),
                    description=poi_data.get("description"),
                    image_url=poi_data.get("image_url"),
                    website_url=poi_data.get("website_url"),
                    rating=poi_data.get("rating"),
                    price_tier=poi_data.get("price_tier"),
                    recommended_duration_mins=poi_data.get("recommended_duration_mins", 120),
                    tod_preference=poi_data.get("tod_preference"),
                    opening_hours=poi_data.get("opening_hours"),
                    needs_reservation=poi_data.get("needs_reservation")
                )
                db.add(new_attraction)
                await db.flush()

                poi_data["id"] = new_attraction.id
            else:
                poi_data["id"] = existing_place.id
            
            updated_resolved_list.append(poi_data)
            
        await db.commit()
    
    return {
        "resolved_attractions": Overwrite(updated_resolved_list),
        "action": "idle"
    }


async def picking_transit(state: ItineraryState) -> dict:
    action = state.get("action")
    location = state.get("data", {}).get("destination") or state.get("search_location", "Unknown Location")
    from_date = state.get("data", {}).get("from_date")
    to_date = state.get("data", {}).get("to_date")
    
    config_dict = state.get("mobility_config")
    if not config_dict:
        config_dict = MobilityConfig.create_default().model_dump(mode='json')
    
    log.info(f"Routing Logistics Action: {action} for {location}")

    if action == "search_public_transport_offers":
        if config_dict.get("strategies", {}).get("public_transport", {}).get("details_loaded"):
            return {"action": "idle"}
        return await _execute_transit_research(from_date, to_date, location, config_dict)
    
    elif action == "search_rental_car_offers":
        if config_dict.get("strategies", {}).get("rental_car", {}).get("details_loaded"):
            return {"action": "idle"}
        return await _execute_rental_research(from_date, to_date, location, config_dict)
    
    elif action == "mobility_recommendation":
        if state.get("mobility_recommendation") is not None:
            return {"action": "idle"}
        attraction_locations = set()
        for poi in state.get("pois", []):
            if poi.get("location"):
                attraction_locations.add(poi["location"])
        return await _execute_mobility_research(from_date, to_date, location, attraction_locations)
    
    elif action == "pace_recommendation":
        if state.get("pace_recommendation") is not None:
            return {"action": "idle"}
        pois = state.get("pois", [])
        return await _execute_pace_research(from_date, to_date, location, pois)

    return {"action": "idle"}

async def _execute_transit_research(from_date: str, to_date: str, location: str, config_dict: dict) -> dict:
    duration_days = 7
    month_year = datetime.now().strftime("%B %Y")

    if from_date and to_date:
        try:
            d1 = datetime.fromisoformat(from_date)
            d2 = datetime.fromisoformat(to_date)
            duration_days = (d2 - d1).days + 1
            month_year = d1.strftime("%B %Y")
        except Exception:
            log.warning("Failed to parse dates for transit research, using defaults.")

    if duration_days <= 1:
        pass_target = "24h / 1-day ticket"
    elif duration_days <= 3:
        pass_target = "48h or 72h tourist passes"
    elif duration_days <= 7:
        pass_target = "weekly pass or 7-day tourist card"
    else:
        pass_target = "monthly or long-term tourist passes"

    search_query = (
        f"official {location} public transport website, "
        f"{location} transport {pass_target} prices {month_year}, "
        f"cost of {duration_days} days of public transit in {location},"
        f"operating hours for {location} public transit, "
    )
    search_results = await search_tool.ainvoke(search_query)

    if isinstance(search_results, list):
        context_text = "\n".join([res.get("content", "") for res in search_results if isinstance(res, dict)])
    else:
        context_text = str(search_results)
    
    structured_llm = llm.with_structured_output(TransitEnrichmentSchema)

    prompt = transit_extraction_prompt.format(
        location=location,
        duration=duration_days,
        dates=f"{from_date} to {to_date}",
        pass_target=pass_target,
        context=context_text
    )

    extracted_data = await structured_llm.ainvoke(prompt)

    config_dict["strategies"]["public_transport"].update({
        "official_link": extracted_data.official_link,
        "pass_price_est": extracted_data.pass_price_est,
        "currency": extracted_data.currency,
        "operating_hours": extracted_data.operating_hours,
        "details_loaded": True 
    })

    return {
        "mobility_config": config_dict,
        "action": "idle",
    }

async def _execute_rental_research(from_date: str, to_date: str, location: str, config_dict: dict) -> dict:
    duration_days = 7
    month_year = datetime.now().strftime("%B %Y")

    if from_date and to_date:
        try:
            d1 = datetime.fromisoformat(from_date)
            d2 = datetime.fromisoformat(to_date)
            duration_days = (d2 - d1).days + 1
            month_year = d1.strftime("%B %Y")
        except Exception:
            log.warning("Failed to parse dates for rental research, using defaults.")

    search_query = (
        f"car rental prices {location} {month_year}, "
        f"is there a ZTL zone in {location} for tourists, "
        f"average daily car rental cost {location}"
    )
    
    search_results = await search_tool.ainvoke(search_query)
    context_text = "\n".join([res.get("content", "") for res in search_results if isinstance(res, dict)])

    structured_llm = llm.with_structured_output(RentalEnrichmentSchema)
    prompt = rental_extraction_prompt.format(
        location=location,
        duration=duration_days,
        dates=f"{from_date} to {to_date}",
        context=context_text
    )

    extracted_data = await structured_llm.ainvoke(prompt)

    config_dict["strategies"]["rental_car"].update({
        "official_link": extracted_data.official_link,
        "daily_price_est": extracted_data.daily_price_est,
        "ztl_warning": extracted_data.ztl_warning,
        "operating_hours": extracted_data.operating_hours,
        "details_loaded": True 
    })

    return {"mobility_config": config_dict, "action": "idle"}

async def _execute_mobility_research(from_date: str, to_date: str, location: str, locations: set) -> dict:

    search_query = (
        f"do tourists in {location} typically rent cars, "
        f"is there a ZTL zone in {location} for tourists, "
        f"average daily car rental cost {location}"
    )
    search_results = await search_tool.ainvoke(search_query)

    if isinstance(search_results, list):
        context_text = "\n".join([res.get("content", "") for res in search_results if isinstance(res, dict)])
    else:
        context_text = str(search_results)

    structured_llm = llm.with_structured_output(MobilityRecommendationSchema)
    prompt = car_rental_recommendation_prompt.format(
        destination=location,
        travel_period=f"{from_date} to {to_date}",
        planned_locations=", ".join(locations),
        web_context=context_text
    )
    
    recommendation = await structured_llm.ainvoke(prompt)

    return {
        "mobility_recommendation": recommendation,
        "action": "idle"
    }

async def _execute_pace_research(from_date: str, to_date: str, location: str, pois: List[dict]) -> dict:
    duration_days = 7
    month_year = datetime.now().strftime("%B %Y")

    if from_date and to_date:
        try:
            d1 = datetime.fromisoformat(from_date)
            d2 = datetime.fromisoformat(to_date)
            duration_days = (d2 - d1).days + 1
            month_year = d1.strftime("%B %Y")
        except Exception:
            log.warning("Failed to parse dates for mobility research, using defaults.")

    formatted_pois = "\n\n".join([
        f"""
    {idx + 1}. {poi.get('name', 'Unknown Attraction')}
    - Bucket: {poi.get('bucket', 'unknown')}
    - Time To Spend: {poi.get('time_to_spend', 0)} minutes
    - Location: {poi.get('location', 'Unknown')}
    """.strip()
        for idx, poi in enumerate(pois)
    ])

    structured_llm = llm.with_structured_output(PaceRecommendationSchema)
    prompt = pace_recommendation_prompt.format(
        destination=location,
        travel_period=f"{from_date} to {to_date}",
        planned_pois=formatted_pois,
    )
    
    recommendation = await structured_llm.ainvoke(prompt)

    return {
        "pace_recommendation": recommendation,
        "action": "idle"
    }
    
async def organize_itinerary(state: ItineraryState) -> dict:
    print("Executing organize_itinerary node...")
    action = state.get("action")
    print(f"Action: {action}")

    if action == "generate_schedule":
        return await _generate_schedule(state)
    elif action == "recalculate_timeline":
        return await _recalculate_timeline(state)
    elif action == "sync_transit":
        return await _sync_transit(state)
    elif action == "explain_dropped":
        return await _explain_dropped(state)
    
    return {}

async def _generate_schedule(state: ItineraryState) -> dict:
    """
    LangGraph node: Fetches physical POI data from DB, merges with user preferences,
    and runs the scheduling engine.
    """
    pois_state = state.get("pois", [])
    pace = state.get("pace", "moderate")
    trip_details = state.get("trip_details")

    if not pois_state or not trip_details:
        return {"schedule": [], "excluded_pois": {}}

    try:
        poi_ids = [p["id"] for p in pois_state]

        async with SessionLocal() as db:
            stmt = select(GlobalAttraction).where(GlobalAttraction.id.in_(poi_ids))
            result = await db.execute(stmt)
            db_attractions = {attr.id: attr for attr in result.scalars().all()}

        engine_pois = []
        for state_poi in pois_state:
            db_poi = db_attractions.get(state_poi["id"])
            if not db_poi:
                continue

            duration = state_poi.get("time_to_spend") or db_poi.recommended_duration_mins
            
            opening_hours_raw = db_poi.opening_hours
            if isinstance(opening_hours_raw, dict):
                opening_hours_str = orjson.dumps(opening_hours_raw)
            else:
                opening_hours_str = opening_hours_raw

            engine_pois.append({
                "id": db_poi.id,
                "name": db_poi.official_name,
                "bucket": state_poi.get("bucket", "want"),
                "latitude": db_poi.latitude,
                "longitude": db_poi.longitude,
                "recommended_duration_mins": duration,
                "opening_hours": opening_hours_str,
                "image_url": db_poi.image_url
            })
            
        #log.info(engine_pois)

        arrival_dt = datetime.fromisoformat(trip_details["arrival_dt"])
        departure_dt = datetime.fromisoformat(trip_details["departure_dt"])
        hotel_coords = trip_details.get("hotel_coords")
        airport_coords = trip_details.get("airport_coords")
        wakeup_time = trip_details.get("wakeup_time", "08:00")
        lunch_duration_mins = trip_details.get("lunch_duration_mins", 90)

        engine = ScheduleEngine(
            pace=pace,
            arrival_dt=arrival_dt,
            departure_dt=departure_dt,
            hotel_coords=hotel_coords,
            airport_coords=airport_coords,
            wakeup_time=wakeup_time,
            lunch_duration_mins=lunch_duration_mins
        )

        result = await anyio.to_thread.run_sync(engine.generate_schedule, engine_pois)
        
        return {
            "schedule": result.get("schedule", []),
            "excluded_pois": result.get("excluded", {})
        }
        
    except Exception as e:
        log.error(f"Schedule Engine Failed: {e}", exc_info=True)
        return {}

async def _recalculate_timeline(state: ItineraryState) -> dict:
    """
    LangGraph Node Action: Bypasses the geographical optimizer.
    Strictly runs the clock simulation on the exact order provided by the user,
    preserving pre-existing synced real transit legs to enable fluid hybrid rendering.
    """
    pois_state = state.get("pois", [])
    trip_details = state.get("trip_details")
    pace = state.get("pace", "moderate")
    user_timeline = state.get("user_timeline")
    old_schedule = state.get("schedule") or []

    if not pois_state or not trip_details or not user_timeline:
        log.warning("Missing data to recalculate timeline.")
        return {}

    existing_transit_legs = {}
    for day in old_schedule:
        events = day.get("events") or []
        last_geo_evt = None  # tracks last event that actually had coordinates
        
        for curr_evt in events:
            lat2 = curr_evt.get("latitude")
            lng2 = curr_evt.get("longitude")
            leg_state = curr_evt.get("transit_leg")
            
            # A verified leg on curr_evt describes the transit FROM the last real
            # geo-located event, skipping any coordinate-less events (meals, etc.)
            if leg_state and leg_state.get("is_verified") and last_geo_evt is not None:
                lat1 = last_geo_evt.get("latitude")
                lng1 = last_geo_evt.get("longitude")
                
                if None not in (lat1, lng1, lat2, lng2):
                    leg_key = f"{lat1:.5f},{lng1:.5f}->{lat2:.5f},{lng2:.5f}"
                    active_mode = leg_state.get("mode", "transit")
                    existing_transit_legs[leg_key] = {
                        "active_mode": active_mode,
                        "alternatives": leg_state.get("alternatives", {})
                    }
            
            # Advance the geo cursor only when this event actually has coordinates
            if lat2 is not None and lng2 is not None:
                last_geo_evt = curr_evt

    try:
        poi_ids = [p["id"] for p in pois_state]

        async with SessionLocal() as db:
            stmt = select(GlobalAttraction).where(GlobalAttraction.id.in_(poi_ids))
            result = await db.execute(stmt)
            db_attractions = {attr.id: attr for attr in result.scalars().all()}

        engine_pois = []
        for state_poi in pois_state:
            db_poi = db_attractions.get(state_poi["id"])
            if not db_poi:
                continue

            duration = state_poi.get("time_to_spend") or db_poi.recommended_duration_mins
            
            opening_hours_raw = db_poi.opening_hours
            if isinstance(opening_hours_raw, dict):
                opening_hours_str = orjson.dumps(opening_hours_raw)
            else:
                opening_hours_str = opening_hours_raw

            engine_pois.append({
                "id": db_poi.id,
                "name": db_poi.official_name,
                "bucket": state_poi.get("bucket", "want"),
                "latitude": db_poi.latitude,
                "longitude": db_poi.longitude,
                "recommended_duration_mins": duration,
                "opening_hours": opening_hours_str,
                "image_url": db_poi.image_url
            })

        arrival_dt = datetime.fromisoformat(trip_details["arrival_dt"])
        departure_dt = datetime.fromisoformat(trip_details["departure_dt"])
        hotel_coords = trip_details.get("hotel_coords")
        airport_coords = trip_details.get("airport_coords")
        wakeup_time = trip_details.get("wakeup_time", "08:00")
        lunch_duration_mins = trip_details.get("lunch_duration_mins", 90)

        engine = ScheduleEngine(
            pace=pace,
            arrival_dt=arrival_dt,
            departure_dt=departure_dt,
            hotel_coords=hotel_coords,
            airport_coords=airport_coords,
            wakeup_time=wakeup_time,
            lunch_duration_mins=lunch_duration_mins
        )

        result = await anyio.to_thread.run_sync(engine.recalculate_user_timeline, user_timeline, engine_pois, existing_transit_legs)

        return {
            "schedule": result.get("schedule", []),
            "excluded_pois": result.get("excluded", {"must": [], "want": [], "optional": []}),
            "action": "idle",
            "user_timeline": None
        }

    except Exception as e:
        log.error(f"Failed to recalculate user timeline: {e}", exc_info=True)
        return {}
    
async def _sync_transit(state: ItineraryState) -> dict:
    print("Executing _sync_transit node processing layer...")
    
    mobility_config = state.get("mobility_config") or {}
    strategies = mobility_config.get("strategies", {})
    rental_car = strategies.get("rental_car", {})
    
    if isinstance(rental_car, dict):
        driving_enabled = rental_car.get("enabled", False)
    else:
        driving_enabled = getattr(rental_car, "enabled", False)

    current_schedule = state.get("schedule") or []
    pois_state = state.get("pois") or []
    
    if not pois_state:
        return {"action": "idle"}
        
    try:
        poi_ids = [p["id"] for p in pois_state]

        async with SessionLocal() as db:
            stmt = select(GlobalAttraction).where(GlobalAttraction.id.in_(poi_ids))
            result = await db.execute(stmt)
            db_attractions = {attr.id: attr for attr in result.scalars().all()}

        engine_pois = []
        for state_poi in pois_state:
            db_poi = db_attractions.get(state_poi["id"])
            if not db_poi:
                continue

            duration = state_poi.get("time_to_spend") or db_poi.recommended_duration_mins
            
            opening_hours_raw = db_poi.opening_hours
            if isinstance(opening_hours_raw, dict):
                opening_hours_str = orjson.dumps(opening_hours_raw)
            else:
                opening_hours_str = opening_hours_raw

            engine_pois.append({
                "id": db_poi.id,
                "name": db_poi.official_name,
                "bucket": state_poi.get("bucket", "want"),
                "latitude": db_poi.latitude,
                "longitude": db_poi.longitude,
                "recommended_duration_mins": duration,
                "opening_hours": opening_hours_str,
                "image_url": db_poi.image_url
            })
    except Exception as e:
        log.error(f"Failed to enrich POIs inside sync transit worker node: {e}", exc_info=True)
        return {}

    tasks = []
    task_keys = []  
    
    def safe_float(val):
        try: return float(val)
        except (ValueError, TypeError): return None

    for day in current_schedule:
        day_date_str = day.get("date")
        is_weekend = False
        if day_date_str:
            try:
                is_weekend = datetime.strptime(day_date_str, "%Y-%m-%d").isoweekday() in [6, 7]
            except Exception:
                pass
                
        events = day.get("events") or []
        
        geo_events = []
        for evt in events:
            lat = safe_float(evt.get("latitude"))
            lng = safe_float(evt.get("longitude"))
            if lat is not None and lng is not None:
                geo_events.append({
                    "latitude": lat,
                    "longitude": lng,
                    "end_time": evt.get("end_time", "08:00"),
                    "id": evt.get("id"),
                })
        
        for i in range(1, len(geo_events)):
            prev_evt = geo_events[i - 1]
            curr_evt = geo_events[i]
            
            lat1, lng1 = prev_evt["latitude"], prev_evt["longitude"]
            lat2, lng2 = curr_evt["latitude"], curr_evt["longitude"]
            
            time_str = prev_evt["end_time"]
            leg_key = f"{lat1:.5f},{lng1:.5f}->{lat2:.5f},{lng2:.5f}"

            origin_name = None
            destination_name = None

            if prev_evt.get("id") == "arr_airport" or "airport" in prev_evt.get("name", "").lower():
                origin_name = state.get('data', {}).get('airport_name')

            if curr_evt.get("id") == "dep_airport" or "airport" in curr_evt.get("name", "").lower():
                destination_name = state.get('data', {}).get('airport_name')
            
            if leg_key not in task_keys:
                task_keys.append(leg_key)
                tasks.append(
                    get_transit_bundle_for_leg(
                        origin_coords=(lat1, lng1),
                        destination_coords=(lat2, lng2),
                        time_str=time_str,
                        is_weekend=is_weekend,
                        driving_enabled=driving_enabled,
                        origin_name=origin_name,
                        destination_name=destination_name
                    )
                )

    routing_results = await asyncio.gather(*tasks) if tasks else []
    
    existing_transit_legs = {}
    for leg_key, bundle_data in zip(task_keys, routing_results):
        if bundle_data:
            default_mode = "driving" if driving_enabled else "transit"
            if default_mode not in bundle_data and bundle_data:
                default_mode = list(bundle_data.keys())[0]
                
            existing_transit_legs[leg_key] = {
                "active_mode": default_mode,
                "alternatives": bundle_data
            }

    user_days_poi_ids = []
    for day in current_schedule:
        day_ids = []
        for event in day.get("events", []):
            evt_id = event.get("id")
            if isinstance(evt_id, int):
                day_ids.append(evt_id)
            elif isinstance(evt_id, str) and evt_id.isdigit():
                day_ids.append(int(evt_id))
        user_days_poi_ids.append(day_ids)

    trip_details = state.get("trip_details") or {}
    
    def parse_coords(val) -> tuple:
        if isinstance(val, (list, tuple)) and len(val) >= 2:
            return (float(val[0]), float(val[1]))
        if isinstance(val, str):
            try:
                parts = val.split(",")
                return (float(parts[0]), float(parts[1]))
            except Exception: pass
        return (0.0, 0.0)

    def parse_dt(val) -> datetime:
        if isinstance(val, datetime): return val
        if isinstance(val, str):
            try: return datetime.fromisoformat(val.replace("Z", ""))
            except Exception: pass
        return datetime.now()

    hotel_coords = parse_coords(trip_details.get("hotel_coords"))
    airport_coords = parse_coords(trip_details.get("airport_coords"))
    arrival_dt = parse_dt(trip_details.get("arrival_dt") or trip_details.get("arrival_time"))
    departure_dt = parse_dt(trip_details.get("departure_dt") or trip_details.get("departure_time"))
    
    pace = state.get("pace") or "Moderate"
    wakeup_time = trip_details.get("wakeup_time", "08:00")
    lunch_duration_mins = trip_details.get("lunch_duration_mins", 90)

    engine = ScheduleEngine(
        pace=pace,
        arrival_dt=arrival_dt,
        departure_dt=departure_dt,
        hotel_coords=hotel_coords,
        airport_coords=airport_coords,
        wakeup_time=wakeup_time,
        lunch_duration_mins=int(lunch_duration_mins)
    )

    recalc_result = await anyio.to_thread.run_sync(engine.recalculate_user_timeline, user_days_poi_ids, engine_pois, existing_transit_legs)

    return {
        "schedule": recalc_result.get("schedule"),
        "excluded_pois": recalc_result.get("excluded"),
        "action": "idle" 
    }

async def _explain_dropped(state: dict) -> dict:
    log.info("Executing _explain_dropped diagnostics pass...")
    
    excluded_pois = dict(state.get("excluded_pois", {}) or {})
    
    all_dropped_pois = []
    for bucket in ["must", "want", "optional"]:
        all_dropped_pois.extend(excluded_pois.get(bucket, []))
        
    if not all_dropped_pois:
        return {"excluded_pois": excluded_pois}

    destination = state.get("destination", "Your Destination")
    from_date = state.get("from_date", "TBD")
    to_date = state.get("to_date", "TBD")
    pace = state.get("pace", "moderate")
    wakeup_time = state.get("wakeup_time", "08:00")
    schedule_context = state.get("schedule", [])

    structured_llm = llm.with_structured_output(ExplanationResponseSchema)
    formatted_prompt = explain_dropped_prompt.format(
        destination=destination,
        dates=f"{from_date} to {to_date}",
        pace=pace,
        wakeup_time=wakeup_time,
        schedule_context=json.dumps(schedule_context, indent=2),
        dropped_context=json.dumps(all_dropped_pois, indent=2)
    )

    extracted_data = await structured_llm.ainvoke(formatted_prompt)
    
    diag_lookup = {str(d.poi_id): d for d in extracted_data.explanations}

    for bucket in ["must", "want", "optional"]:
        if bucket in excluded_pois:
            for item in excluded_pois[bucket]:
                item_id_str = str(item.get("id", ""))
                if item_id_str in diag_lookup:
                    diag = diag_lookup[item_id_str]
                    item["reason"] = diag.reason
                    item["suggestions"] = [
                        {
                            "action_type": opt.action_type,
                            "label": opt.label,
                            "target_swap_id": opt.target_swap_id
                        } for opt in diag.suggestions
                    ]

    return {"action": "idle", "excluded_pois": excluded_pois}

if __name__ == "__main__":
    print("This module is not meant to be run directly. It provides the agent nodes and decisional edges.")
