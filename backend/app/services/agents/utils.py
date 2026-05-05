from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from app.models.vacation_session import VacationSession
from app.models.vacation import Vacation
from app.services.agents.memory import DiscoveryState, ItineraryState
from app.utils.generic import calculate_age
import httpx
from typing import Optional


async def get_formatted_travel_history(db: AsyncSession, user_id: str) -> str:
    """
    Fetches the user's past 5 trips and formats them into a lightweight string 
    for the LLM context window.
    """
    stmt = select(Vacation).where(
        Vacation.user_id == user_id
    ).order_by(Vacation.created_at.desc()).limit(5)
    
    result = await db.execute(stmt)
    vacations = result.scalars().all()

    if not vacations:
        return "No prior travel history recorded with us."

    history_lines = []
    for v in vacations:
        line = f"- {v.destination}"
        if v.from_date and v.to_date:
            line += f" ({v.from_date} to {v.to_date})"
        if getattr(v, 'people_count', None):
            line += f" with {v.people_count} travelers"
        history_lines.append(line)

    return "\n".join(history_lines)

def format_extracted_data(session: VacationSession) -> dict:
    """Formats the session DB model into the standard extracted_data dictionary."""
    return {
        "departure": session.departure,
        "destination": session.destination,
        "from_date": session.from_date.isoformat() if session.from_date else None,
        "to_date": session.to_date.isoformat() if session.to_date else None,
        "adults": session.adults,
        "children": session.children,
        "infants_in_seat": session.infants_in_seat,
        "infants_on_lap": session.infants_on_lap,
        "children_ages": session.children_ages,
        "room_qty": session.room_qty,
        "currency": session.currency,
        "budget": session.budget
    }

async def get_resumed_state(db: AsyncSession, session_id: int) -> dict:
    """
    Performs a fast, single-table query to fetch the latest trip parameters.
    Used to sync UI changes into the graph when resuming an existing session.
    """
    result = await db.execute(select(VacationSession).filter_by(id=session_id))
    session = result.scalars().first()
    
    if not session:
        raise ValueError(f"Session {session_id} not found")
        
    return format_extracted_data(session)

async def get_initial_state(db: AsyncSession, session_id: int) -> DiscoveryState:
    """
    Fetches session data and returns a DiscoveryState object 
    ready for LangGraph execution.
    """
    stmt = (
        select(VacationSession)
        .options(
            selectinload(VacationSession.user),
            selectinload(VacationSession.companions)
        )
        .filter(VacationSession.id == session_id)
    )
    result = await db.execute(stmt)
    session = result.scalars().first()

    if not session:
        raise ValueError(f"Session {session_id} not found")

    user_bio = session.user.user_description or "No preferences provided."
    persona = f"MAIN TRAVELER ({calculate_age(session.user.date_of_birth)}) BIO: {user_bio}\n\n"
    
    if session.companions:
        persona += "COMPANIONS:\n"
        for comp in session.companions:
            persona += f"- {comp.name} ({calculate_age(comp.date_of_birth)}): {comp.description or 'No bio available.'}\n"

    user_history_str = await get_formatted_travel_history(db, str(session.user_id))

    return {
        "messages": [], 
        "user_id": str(session.user_id),
        "session_id": session.id,
        "persona_context": persona,
        "user_history": user_history_str,
        "extracted_data": {
            "departure": session.departure,
            "destination": session.destination,
            "from_date": session.from_date.isoformat() if session.from_date else None,
            "to_date": session.to_date.isoformat() if session.to_date else None,
            "adults": session.adults,
            "children": session.children,
            "infants_in_seat": session.infants_in_seat,
            "infants_on_lap": session.infants_on_lap,
            "children_ages": session.children_ages,
            "room_qty": session.room_qty,
            "currency": session.currency,
            "budget": session.budget
        },
        "newly_extracted_data": None,
        "is_complete": False
    }

async def resolve_location(query: str) -> str:
    """
    Calls Nominatim (OSM) to turn messy user input into a 
    standardized 'City, CC' string.
    """
    url = f"https://nominatim.openstreetmap.org/search?format=json&q={query}&addressdetails=1&limit=1"
    headers = {
        "User-Agent": "TuRAG/1.0 (contact.turag@gmail.com)",
        "Accept-Language": "en"
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers, timeout=5.0)
            if response.status_code == 200:
                data = response.json()
                if data:
                    result = data[0]
                    address = result.get("address", {})
                    
                    city = (address.get("city") or 
                            address.get("town") or 
                            address.get("village") or 
                            address.get("municipality") or
                            address.get("state"))
                    
                    country_code = address.get("country_code")
                    
                    if city and country_code:
                        print(f"Resolved '{query}' to '{city}, {country_code.upper()}'")
                        return f"{city}, {country_code.upper()}"
                    
                    return result.get("display_name", query)
    except Exception as e:
        print(f"Location resolution error: {e}")


    return query.upper()


def is_llm_null(value) -> bool:
    """
    Catches actual None types and LLM-hallucinated string versions of null.
    Intentionally allows empty strings ("") and 0 to pass through.
    """
    if value is None:
        return True
        
    if isinstance(value, str):
        cleaned_val = value.strip().lower()
        if cleaned_val in {"null", "none", "undefined"}:
            return True
            
    return False

async def get_initial_itinerary_state(db: AsyncSession, session_id: int) -> ItineraryState:
    """
    Fetches session data and returns an ItineraryState object 
    ready for LangGraph execution in the Itinerary phase.
    """
    stmt = (
        select(VacationSession)
        .options(
            selectinload(VacationSession.user),
            selectinload(VacationSession.companions)
        )
        .filter(VacationSession.id == session_id)
    )
    result = await db.execute(stmt)
    session = result.scalars().first()

    if not session:
        raise ValueError(f"Session {session_id} not found")

    user_bio = session.user.user_description or "No preferences provided."
    persona = f"MAIN TRAVELER ({calculate_age(session.user.date_of_birth)}) BIO: {user_bio}\n\n"
    
    if session.companions:
        persona += "COMPANIONS:\n"
        for comp in session.companions:
            persona += f"- {comp.name} ({calculate_age(comp.date_of_birth)}): {comp.description or 'No bio available.'}\n"

    itinerary_db_context = {
        "departure": session.departure,
        "destination": session.destination,
        "from_date": session.from_date.isoformat() if session.from_date else None,
        "to_date": session.to_date.isoformat() if session.to_date else None,
        "destination_arrival": session.destination_arrival.isoformat() if session.destination_arrival else None,
        "destination_departure": session.destination_departure.isoformat() if session.destination_departure else None,
        "adults": session.adults,
        "children": session.children,
        "infants_in_seat": session.infants_in_seat,
        "infants_on_lap": session.infants_on_lap,
        "room_qty": session.room_qty,
        "currency": session.currency,
        "budget": session.budget,
        "flight_price": session.flight_price,
        "accomodation_price": session.accomodation_price
    }

    return {
        "messages": [], 
        "user_id": str(session.user_id),
        "session_id": session.id,
        "persona_context": persona,
        "data": itinerary_db_context,
        "daily_themes": {},
        "daily_plans": {},
        "daily_links": {},
        "are_themes_confirmed": False
    }