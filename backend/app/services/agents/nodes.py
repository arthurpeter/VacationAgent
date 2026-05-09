import asyncio
from typing import Literal

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

async def picking_attractions(state: ItineraryState) -> dict:
    action = state.get("action")
    
    destination = state.get("data", {}).get("destination", "").split(",")
    if len(destination) < 2:
        log.error("Invalid destination format in state['data']['destination']")
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
            "id": p.id # Database Primary Key
        }

    if action == "initial_fetch":
        log.info(f"Starting Initial Fetch for {city}, {country}...")
        
        async with SessionLocal() as db:
            stmt = select(GlobalAttraction).where(
                GlobalAttraction.city.ilike(f"%{city}%") & 
                GlobalAttraction.country.ilike(f"%{country}%")
            ).limit(20)
            result = await db.execute(stmt)
            existing_places = result.scalars().all()

            if len(existing_places) >= 10:
                log.info(f"CACHE HIT: Showing {len(existing_places)} existing places from DB.")
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

            for name in attraction_names:
                poi_data = await autosuggest_places(name, coords["lat"], coords["lon"], limit=1)
                if not poi_data: continue
                
                xid = poi_data[0]["xid"]
                stmt = select(GlobalAttraction).where(GlobalAttraction.external_place_id == xid)
                res = await db.execute(stmt)
                cached = res.scalars().first()

                if cached:
                    db_hits.append(format_cached_poi(cached))
                else:
                    resolved = await get_place_details(xid)
                    if resolved:
                        resolved["city"] = city
                        resolved["country"] = country 
                        new_finds.append(resolved)
                
                await asyncio.sleep(0.5)

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
                else:
                    log.info(f"NEW ATTRACTION: {name} not in DB, fetching OTM details...")
                    resolved = await get_place_details(xid)
                    if resolved:
                        resolved["city"] = city
                        resolved["country"] = country 
                        new_finds.append(resolved)
                
                await asyncio.sleep(0.5)

        updates.update({
            "unresolved_attractions": new_finds,
            "resolved_attractions": Overwrite(db_hits),
            "action": "resolve_attractions" if new_finds else "idle"
        })
                    
    return updates
    
async def enrich_single_attraction_node(poi_data: dict) -> dict:
    name = poi_data.get("official_name", "Unknown Place")
    otm_city = poi_data.get("city", "Unknown City")
    otm_country = poi_data.get("country", "Unknown")
    otm_description = poi_data.get("description", "No description available.")
    
    search_tool = TavilySearch(max_results=3, tavily_api_key=settings.TAVILY_API_KEY)
    search_query = f"{name} in {otm_city} {otm_country} official website, ticket price, recommended duration, visitor reviews star rating"
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
        "country": extracted_data.country
    }

    return {"resolved_attractions": [enriched_poi]}

async def save_attractions_to_db(state: ItineraryState) -> dict:
    resolved = state.get("resolved_attractions", [])
    if not resolved:
        return {"action": "move_to_next_stage"}

    new_formatted_pois = []
    
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
                    tod_preference=poi_data.get("tod_preference")
                )
                db.add(new_attraction)
                await db.flush()
            
        await db.commit()
    
    return {"action": "idle"}


async def picking_transit(state: ItineraryState) -> dict:
    print("Executing picking_transit node...")
    return {}

async def organizing_days(state: ItineraryState) -> dict:
    print("Executing organizing_days node...")
    return {}

async def organizing_attractions(state: ItineraryState) -> dict:
    print("Executing organizing_attractions node...")
    return {}

if __name__ == "__main__":
    print("This module is not meant to be run directly. It provides the agent nodes and decisional edges.")
