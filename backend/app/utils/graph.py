from app.services.agents.memory import GraphMemory, UserInfo, TripDetails
from app.core.database import SessionLocal
from app.models.user import User
from app.utils.generic import calculate_age
from app.services.agents.responses import InformationCollectorResponse
from langgraph.store.base import BaseStore

from copy import deepcopy

def generate_memory_from_db(uid: str):
    """
    Fetch user and trip info from the database and build a State object.
    Args:
        uid (str): The user's unique identifier.
    Returns:
        State: The constructed state for the agent.
    """
    db = SessionLocal()
    user_data = db.query(User).filter(User.id == uid).first()
    db.close()

    if not user_data:
        raise ValueError("User not found in database.")

    user_info = UserInfo(
        first_name=user_data.first_name,
        email=user_data.email,
        age=calculate_age(user_data.date_of_birth),
        user_description=getattr(user_data, "user_description", None),
        location=getattr(user_data, "location", None),
    )
    trip_details = TripDetails(
        location=user_info.location,
        destination=None,
        departure_date=None,
        return_date=None,
        budget=None,
        adults=None,
        children=None,
        description=None
    )
    return GraphMemory(trip_details=trip_details, user_info=user_info)

def update_memory(uid: str, memory: BaseStore, result: InformationCollectorResponse) -> bool:
    """
    Update the memory with the information collected from the user.
    Args:
        uid (str): The user's unique identifier.
        memory (GraphMemory): The current memory state.
        result (InformationCollectorResponse): The response from the information collector.
    """
    old_memory = memory.get(namespace="user_trip_information", key=uid).value

    new_memory = deepcopy(old_memory)
    # new_memory = old_memory.copy(deep=True)

    new_memory.trip_details.description = result.description if result.description else new_memory.trip_details.description
    new_memory.trip_details.departure_date = result.departure_date if result.departure_date else new_memory.trip_details.departure_date
    new_memory.trip_details.return_date = result.return_date if result.return_date else new_memory.trip_details.return_date
    new_memory.trip_details.budget = result.budget if result.budget else new_memory.trip_details.budget
    new_memory.trip_details.adults = result.adults if result.adults else new_memory.trip_details.adults
    new_memory.trip_details.children = result.children if result.children else new_memory.trip_details.children
    new_memory.user_info.user_description = result.user_description if result.user_description else new_memory.user_info.user_description

    memory.put(namespace="user_trip_information", key=uid, value=new_memory)

    return new_memory != old_memory