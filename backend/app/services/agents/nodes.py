from typing import Literal

from app.services.agents.memory import DiscoveryState, ItineraryState
from app.services.agents.prompts import *
from langgraph.store.base import BaseStore
from langgraph.graph import END

from app.services.agents.responses import ArchitectResult, ExtractionResult, DetailerResult, SubmitLinks
from app.core.config import settings

from datetime import datetime
from sqlalchemy import update, select
from app.core.database import SessionLocal
from app.models.vacation_session import VacationSession
from app.services.agents.utils import is_llm_null, resolve_location, get_resumed_state
from langchain_core.messages import RemoveMessage, SystemMessage
from app.services.agents.tools import responder_tools, link_finder_tools


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
        children_from_ages = len([a for a in ages_list if 2 <= a < 12])
        
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
    
    system_instructions = responder_prompt.format(
        persona=persona,
        current_data=current_data,
        missing_fields=missing_fields,
        is_complete=is_complete,
        passengers_confirmed=passengers_confirmed,
        history=history_str
    )

    llm_with_tools = llm.bind_tools(responder_tools)
    
    response = await llm_with_tools.ainvoke([SystemMessage(content=system_instructions)] + current_messages)
    
    return {"messages": [response]}

if __name__ == "__main__":
    print("This module is not meant to be run directly. It provides the agent nodes and decisional edges.")


# Itinerary Graph Nodes

async def global_architect(state: ItineraryState) -> dict:
    """
    Node 1: Takes the complete trip parameters and formulates a high-level itinerary.
    """
    trip_data = state.get("data", {})
    trip_data_str = "\n".join([f"- {k}: {v}" for k, v in trip_data.items() if v is not None])

    current_themes_dict = state.get("daily_themes") or {}
    if current_themes_dict:
        current_themes_str = "\n".join([f"Day {day}: {theme}" for day, theme in current_themes_dict.items()])
    else:
        current_themes_str = "No themes generated yet. You must generate the initial sketch."

    messages = state.get("messages", [])
    recent_msgs = messages[-4:] if len(messages) >= 4 else messages
    chat_context = ""
    for msg in recent_msgs:
        role = "User" if msg.type == "human" else "Assistant"
        chat_context += f"{role}: {msg.content}\n"

    instructions = itinerary_architect_prompt.format(
        persona=state.get("persona_context", "Unknown traveler"),
        trip_data=trip_data_str,
        current_themes=current_themes_str,
        chat_history=chat_context.strip() or "No conversation yet."
    )

    structured_llm = llm.with_structured_output(ArchitectResult)
    response: ArchitectResult = await structured_llm.ainvoke(instructions)

    new_themes = dict(current_themes_dict)
    for item in response.themes:
        new_themes[item.day_number] = item.theme

    return {"daily_themes": new_themes}

async def focused_detailer(state: ItineraryState) -> dict:
    """
    Node 2: Takes the high-level itinerary and fills in detailed recommendations.
    """
    trip_data = state.get("data", {})
    trip_data_str = "\n".join([f"- {k}: {v}" for k, v in trip_data.items() if v is not None])

    current_themes_dict = state.get("daily_themes") or {}
    themes_str = "\n".join([f"Day {day}: {theme}" for day, theme in current_themes_dict.items()]) if current_themes_dict else "No themes available."

    current_plans_dict = state.get("daily_plans") or {}
    plans_str = "\n".join([f"Day {day}:\n{plan}" for day, plan in current_plans_dict.items()]) if current_plans_dict else "No detailed plans generated yet."

    messages = state.get("messages", [])
    recent_msgs = messages[-4:] if len(messages) >= 4 else messages
    chat_context = ""
    for msg in recent_msgs:
        role = "User" if msg.type == "human" else "Assistant"
        chat_context += f"{role}: {msg.content}\n"

    instructions = itinerary_detailer_prompt.format(
        trip_data=trip_data_str,
        current_themes=themes_str,
        current_plans=plans_str,
        chat_history=chat_context.strip() or "No conversation yet."
    )

    structured_llm = llm.with_structured_output(DetailerResult)
    response: DetailerResult = await structured_llm.ainvoke(instructions)

    new_plans = dict(current_plans_dict)
    
    new_plans[response.day_number] = response.detailed_plan

    return {
        "daily_plans": new_plans,
        "recently_detailed_days": [response.day_number]
    }

async def link_finder(state: ItineraryState) -> dict:
    """
    Node 3: A tool node that finds relevant links for itinerary items.
    """
    target_days = state.get("recently_detailed_days") or []
    if not target_days:
        return {}
    
    target_day = target_days[0]
    current_plans_dict = state.get("daily_plans") or {}
    plan_text = current_plans_dict.get(target_day, "No plan found.")

    instructions = link_finder_prompt.format(
        target_day=target_day,
        plan_text=plan_text
    )

    messages = state.get("messages", [])
    tool_loop_messages = []
    
    for msg in reversed(messages):
        if msg.type == "human":
            break
        tool_loop_messages.insert(0, msg)

    llm_with_tools = llm.bind_tools(link_finder_tools + [SubmitLinks])
    
    response = await llm_with_tools.ainvoke([SystemMessage(content=instructions)] + tool_loop_messages)
    
    return {"messages": [response]}

async def save_links_and_cleanup(state: ItineraryState) -> dict:
    """Node 3.5: Intercepts SubmitLinks, saves data, and wipes the search history."""
    messages = state.get("messages", [])
    last_message = messages[-1]

    tool_call = last_message.tool_calls[0]
    args = tool_call["args"]

    current_links = state.get("daily_links") or {}
    new_links = dict(current_links)
    new_links[args["day_number"]] = args["links"]

    messages_to_remove = []
    
    for msg in reversed(messages):
        if msg.type == "human":
            break
        if getattr(msg, "id", None):
            messages_to_remove.append(RemoveMessage(id=msg.id))

    return {
        "daily_links": new_links,
        "recently_detailed_days": [],
        "messages": messages_to_remove
    }

async def itinerary_responder(state: ItineraryState) -> dict:
    """
    Node 4: Formulates the final response to the user with the complete itinerary.
    """
    is_phase2 = state.get("are_themes_confirmed", False)
    all_messages = state.get("messages", [])

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

    current_themes_dict = state.get("daily_themes") or {}
    themes_str = "\n".join([f"Day {d}: {t}" for d, t in current_themes_dict.items()]) if current_themes_dict else "No themes generated yet."

    if not is_phase2:
        instructions = itinerary_responder_phase_1_prompt.format(
            current_themes=themes_str,
            chat_history=history_str.strip() or "No conversation yet."
        )
    else:
        instructions = itinerary_responder_phase_2_prompt

    response = await llm.ainvoke([SystemMessage(content=instructions)] + current_messages)

    return {"messages": [response]}