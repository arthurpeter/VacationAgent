from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from app.models.vacation_session import VacationSession
from app.services.agents.memory import DiscoveryState
from app.utils.generic import calculate_age
import httpx
from typing import Optional

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

    return {
        "messages": [], 
        "user_id": str(session.user_id),
        "session_id": session.id,
        "persona_context": persona,
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
    headers = {"User-Agent": "TuRAG/1.0 (contact.turag@gmail.com)"}

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
                        return f"{city}, {country_code.upper()}"
                    
                    return result.get("display_name", query)
    except Exception as e:
        print(f"Location resolution error: {e}")
        
    return query.upper()