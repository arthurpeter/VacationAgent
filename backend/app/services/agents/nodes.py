from typing import Literal
from dotenv import load_dotenv

from app.services.agents.memory import DiscoveryState, State
from app.services.agents.prompts import *
from langgraph.store.base import BaseStore
from langgraph.graph import END

from app.services.agents.responses import ExtractionResult
from app.core.config import settings

from datetime import datetime
from sqlalchemy import update, select
from app.core.database import SessionLocal
from app.models.vacation_session import VacationSession
from app.services.agents.utils import resolve_location


load_dotenv()

llm = settings.llm

async def information_collector(state: DiscoveryState) -> dict:
    """
    Node 1: Parses the user's message and extracts new trip parameters 
    into a transient buffer.
    """
    current_knowledge = "\n".join([
        f"- {k}: {v}" for k, v in state.get("extracted_data", {}).items() if v is not None
    ]) if state.get("extracted_data") else "No information collected yet."

    instructions = information_collector_prompt.format(
        persona=state.get("persona_context", "None"),
        current_knowledge=current_knowledge,
        user_query=state["messages"][-1].content
    )

    structured_llm = llm.with_structured_output(ExtractionResult)
    response = await structured_llm.ainvoke(instructions)
    
    return {"newly_extracted_data": response.model_dump()}


async def db_validator(state: DiscoveryState) -> dict:
    """
    Node 3: Validates the extracted trip parameters and adds them to the database.
    """
    new_info = state.get("newly_extracted_data") or {}
    session_id = state.get("session_id")
    user_id = state.get("user_id")

    if new_info:
        update_values = {}
        for k, v in new_info.items():
            if v is None or k == "is_change_request": continue
            
            if k in ["departure", "destination"]:
                if not v or len(v) < 3: continue
                v = await resolve_location(str(v))
            
            if k in ["from_date", "to_date"] and isinstance(v, str):
                try:
                    v = datetime.strptime(v, "%Y-%m-%d")
                except ValueError: continue
            
            update_values[k] = v

        if update_values:
            async with SessionLocal() as db:
                await db.execute(
                    update(VacationSession)
                    .where(VacationSession.id == session_id, VacationSession.user_id == user_id)
                    .values(**update_values)
                )
                await db.commit()

    async with SessionLocal() as db:
        result = await db.execute(select(VacationSession).filter_by(id=session_id))
        session = result.scalars().first()

    refreshed_data = {
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
        "currency": session.currency
    }

    is_valid = False
    mandatory = ["departure", "destination", "from_date", "to_date"]
    
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
        children_from_ages = len([a for a in ages_list if 2 <= a < 12])
        
        infant_total_count = (refreshed_data.get("infants_in_seat") or 0) + (refreshed_data.get("infants_on_lap") or 0)
        child_total_count = refreshed_data.get("children") or 0

        consistency_ok = (infants_from_ages == infant_total_count and children_from_ages == child_total_count)

        if basic_logic and consistency_ok:
            is_valid = True

    return {
        "extracted_data": refreshed_data,
        "is_complete": is_valid
    }

def should_get_more_info(state: DiscoveryState) -> Literal["next_node", "other_node"]:
    if state["need_information"]:
        return "other_node"
    return "next_node"

if __name__ == "__main__":
    print("This module is not meant to be run directly. It provides the agent nodes and decisional edges.")
