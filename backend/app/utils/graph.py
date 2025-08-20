from app.services.agents.memory import State, UserInfo, TripDetails
from app.core.database import SessionLocal
from app.models.user import User

def generate_state_from_db(uid: str):
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
        username=user_data.username,
        email=user_data.email,
        age=getattr(user_data, "age", None),
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
    )
    return State(trip_details=trip_details, user_info=user_info)     
    