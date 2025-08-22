from app.services.agents.memory import GraphMemory, UserInfo, TripDetails
from app.core.database import SessionLocal
from app.models.user import User
from app.utils.generic import calculate_age
from app.services.agents.responses import InformationCollectorResponse
from langgraph.store.base import BaseStore

def generate_memory_from_db(uid: str, test_mode: bool = False) -> GraphMemory:
    """
    Fetch user and trip info from the database and build a State object.
    Args:
        uid (str): The user's unique identifier.
    Returns:
        State: The constructed state for the agent.
    """
    if test_mode:
        user_info = UserInfo(
            first_name="Test",
            email="test@example.com",
            age=30,
            user_description=None,
            location="Bucharest"
        )
        trip_details = TripDetails(
            location="Bucharest",
            destination=None,
            departure_date=None,
            return_date=None,
            budget=None,
            adults=None,
            children=None,
            description=None
        )
        return GraphMemory(trip_details=trip_details, user_info=user_info)

    db = SessionLocal()
    user_data = db.query(User).filter(User.id == uid).first()
    db.close()

    if not user_data:
        raise ValueError("User not found in database.")

    user_info = UserInfo(
        first_name=getattr(user_data, "first_name", None),
        email=getattr(user_data, "email", None),
        age=calculate_age(user_data.date_of_birth),
        user_description=getattr(user_data, "user_description", None),
        location=getattr(user_data, "location", None),
    )
    trip_details = TripDetails(
        location=getattr(user_info, "location", None),
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

    Returns:
        bool: True if the memory was filled, False otherwise.
    """
    user_memory = memory.get(namespace="user_trip_information", key=uid).value

    # Use attribute access for Pydantic models
    user_memory["trip_details"].description = result.description if result.description else user_memory["trip_details"].description
    user_memory["trip_details"].departure_date = result.departure_date if result.departure_date else user_memory["trip_details"].departure_date
    user_memory["trip_details"].return_date = result.return_date if result.return_date else user_memory["trip_details"].return_date
    user_memory["trip_details"].budget = result.budget if result.budget else user_memory["trip_details"].budget
    user_memory["trip_details"].adults = result.adults if result.adults else user_memory["trip_details"].adults
    user_memory["trip_details"].children = result.children if result.children else user_memory["trip_details"].children
    user_memory["user_info"].user_description = result.user_description if result.user_description else user_memory["user_info"].user_description

    memory.put(namespace="user_trip_information", key=uid, value=user_memory)

    # Example usage:
    trip_full = all(value is not None for value in user_memory["trip_details"].dict().values())
    user_full = all(value is not None for value in user_memory["user_info"].dict().values())

    return trip_full and user_full