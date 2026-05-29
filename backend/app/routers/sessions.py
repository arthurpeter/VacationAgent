from pydantic import BaseModel
from datetime import datetime
from app.schemas.vacation import SessionDataUpdate
from app.core.database import get_checkpointer, get_db
from fastapi import APIRouter, Depends, HTTPException
from app import schemas, models
from app.core.logger import get_logger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from authx import TokenPayload
from app.core.auth import access_token_header
from app.models.vacation_session import SessionStage
from app.models.companion import TravelCompanion
from sqlalchemy.orm import selectinload
from fastapi import BackgroundTasks
from app.routers.notifications import get_db_context
from app.services.agents.itinerary_graph import generate_graph as generate_itinerary_graph

from app.services.email.itinerary_email import send_vacation_blueprint_email

log = get_logger(__name__)

router = APIRouter(prefix="/session", tags=["Session Management"])

@router.patch("/{session_id}/details")
async def update_session_details(
    session_id: int,
    data: SessionDataUpdate,
    db: AsyncSession = Depends(get_db),
    access_token: TokenPayload = Depends(access_token_header)
):
    stmt = select(models.VacationSession).options(
        selectinload(models.VacationSession.companions)
    ).filter_by(
        id=session_id, user_id=access_token.sub
    )
    result = await db.execute(stmt)
    session = result.scalars().first()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    update_data = data.model_dump(exclude_unset=True)

    if "companion_ids" in update_data:
        companion_ids = update_data.pop("companion_ids")
        comp_stmt = select(TravelCompanion).filter(
            TravelCompanion.id.in_(companion_ids),
            TravelCompanion.user_id == access_token.sub
        )
        comp_result = await db.execute(comp_stmt)
        session.companions = comp_result.scalars().all()

    fmt = "%Y-%m-%d"
    if "from_date" in update_data and update_data["from_date"]:
        update_data["from_date"] = datetime.strptime(update_data["from_date"], fmt)
    if "to_date" in update_data and update_data["to_date"]:
        update_data["to_date"] = datetime.strptime(update_data["to_date"], fmt)

    for key, value in update_data.items():
        setattr(session, key, value)

    await db.commit()
    return {"status": "success", "message": "Session updated with companions"}

class StageUpdate(BaseModel):
    stage: SessionStage

@router.patch("/{session_id}/stage")
async def update_session_stage(
    session_id: int,
    update: StageUpdate,
    db: AsyncSession = Depends(get_db),
    access_token: TokenPayload = Depends(access_token_header)
):
    """Updates the user's progress stage."""
    stmt = select(models.VacationSession).filter_by(
        id=session_id, user_id=access_token.sub
    )
    result = await db.execute(stmt)
    session = result.scalars().first()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    session.current_stage = update.stage
    await db.commit()

    return {"status": "success", "current_stage": session.current_stage}

@router.post("/create")
async def create_vacation_session(
    db: AsyncSession = Depends(get_db),
    access_token: TokenPayload = Depends(access_token_header)
    ):
    """Create a new vacation session for the authenticated user."""
    log.info(f"Creating vacation session for user: {access_token.sub}")
    new_session = models.VacationSession(
        user_id=access_token.sub
    )
    db.add(new_session)
    await db.commit()
    await db.refresh(new_session)
    return {"session_id": new_session.id}

@router.get("/getSessions")
async def get_sessions(
    db: AsyncSession = Depends(get_db),
    access_token: TokenPayload = Depends(access_token_header)
    ):
    """Retrieve all vacation sessions for the authenticated user."""
    log.info(f"Retrieving all vacation sessions for user: {access_token.sub}")
    stmt = select(models.VacationSession).filter_by(
        user_id=access_token.sub
    )
    result = await db.execute(stmt)
    sessions = result.scalars().all()
    ids = [session.id for session in sessions]
    return {"session_ids": ids}

@router.post("/compile/{session_id}")
async def compile_session(
    session_id: int,
    db: AsyncSession = Depends(get_db),
    checkpointer = Depends(get_checkpointer),
    token: TokenPayload = Depends(access_token_header)
):
    """
    Compiles active session data and LangGraph thread states into a single, 
    pre-parsed immutable snapshot stored in the vacations table.
    """
    stmt = select(models.VacationSession).where(
        models.VacationSession.id == session_id,
        models.VacationSession.user_id == token.sub
    )
    session = (await db.execute(stmt)).scalar_one_or_none()
    
    if not session:
        raise HTTPException(status_code=404, detail="Active vacation session not found for user")
    
    raw_schedule = []
    mobility_config = {}
    
    try:
        graph = generate_itinerary_graph(checkpointer)
        config = {"configurable": {"thread_id": f"itinerary_{session_id}"}}
        current_state = await graph.aget_state(config)
        
        if current_state and current_state.values:
            raw_schedule = current_state.values.get("schedule", [])
            mobility_config = current_state.values.get("mobility_config", {}).get("strategies", {})
    except Exception as graph_err:
        log.warning(f"LangGraph state not initialized or missing for session {session_id}: {str(graph_err)}")

    rental_car_data = mobility_config.get("rental_car", {})
    public_transport_data = mobility_config.get("public_transport", {})
    
    has_rental_car = rental_car_data.get("enabled", False)
    
    if has_rental_car:
        mobility_payload = {
            "has_rental_car": True,
            "official_link": rental_car_data.get("official_link"),
            "price_est": rental_car_data.get("daily_price_est"),
            "currency": rental_car_data.get("currency"),
            "operating_hours": rental_car_data.get("operating_hours")
        }
    else:
        mobility_payload = {
            "has_rental_car": False,
            "official_link": public_transport_data.get("official_link"),
            "price_est": public_transport_data.get("pass_price_est"),
            "currency": public_transport_data.get("currency"),
            "operating_hours": public_transport_data.get("operating_hours")
        }

    attraction_ids = set()
    for day in raw_schedule:
        for event in day.get("events", []):
            if event.get("type") == "attraction" and isinstance(event.get("id"), int):
                attraction_ids.add(event["id"])

    attraction_map = {}
    if attraction_ids:
        attr_stmt = select(models.GlobalAttraction).where(models.GlobalAttraction.id.in_(list(attraction_ids)))
        attr_res = await db.execute(attr_stmt)
        attraction_map = {a.id: a for a in attr_res.scalars().all()}

    cleaned_timeline = []
    for day in raw_schedule:
        cleaned_events = []
        for event in day.get("events", []):
            event_type = event.get("type")
            event_id = event.get("id")
            
            base_event = {
                "id": event_id,
                "type": event_type,
                "name": event.get("name"),
                "start_time": event.get("start_time"),
                "end_time": event.get("end_time"),
                "transit_mins": event.get("transit_mins", 0)
            }

            if event_type == "attraction" and isinstance(event_id, int) and event_id in attraction_map:
                global_poi = attraction_map[event_id]
                base_event.update({
                    "name": global_poi.official_name,
                    "image_url": global_poi.image_url,
                    "description": global_poi.description,
                    "website_url": global_poi.website_url,
                    "formatted_address": global_poi.formatted_address,
                    "needs_reservation": global_poi.needs_reservation,
                    "rating": global_poi.rating,
                    "formatted_address": global_poi.formatted_address,
                    "city": global_poi.city,
                    "country": global_poi.country
                })

            transit_leg = event.get("transit_leg")
            if transit_leg and transit_leg.get("is_verified"):
                active_mode = transit_leg.get("mode", "transit")
                alternatives = transit_leg.get("alternatives", {})
                mode_data = alternatives.get(active_mode) if alternatives else transit_leg
                
                if mode_data:
                    base_event["transit_path"] = {
                        "mode": active_mode,
                        "duration_mins": mode_data.get("duration_mins", event.get("transit_mins", 0)),
                        "distance_text": mode_data.get("distance_text"),
                        "steps": mode_data.get("steps", [])
                    }

            cleaned_events.append(base_event)

        cleaned_timeline.append({
            "day_index": day.get("day_index"),
            "date": day.get("date"),
            "events": cleaned_events
        })

    itinerary_data_payload = {
        "meta": {
            "compiled_at": datetime.utcnow().isoformat(),
            "currency": session.currency
        },
        "mobility": mobility_payload,
        "timeline": cleaned_timeline
    }

    vacation_stmt = select(models.Vacation).where(models.Vacation.session_id == session.id)
    vacation_record = (await db.execute(vacation_stmt)).scalar_one_or_none()

    # formatted_from = session.from_date.strftime("%b %d, %Y") if session.from_date else "TBD"
    # formatted_to = session.to_date.strftime("%b %d, %Y") if session.to_date else "TBD"

    if vacation_record:
        vacation_record.destination = session.destination
        vacation_record.origin = session.departure
        vacation_record.from_date = session.from_date
        vacation_record.to_date = session.to_date
        vacation_record.adults = session.adults or 1
        vacation_record.children = session.children or 0
        vacation_record.flights_url = session.flights_url
        vacation_record.flight_price = session.flight_price
        vacation_record.flight_ccy = session.flight_ccy
        vacation_record.airport_name = session.airport_name
        vacation_record.accommodation_url = session.accommodation_url
        vacation_record.accommodation_price = session.accommodation_price
        vacation_record.accommodation_ccy = session.accommodation_ccy
        vacation_record.accommodation_name = session.accommodation_name
        vacation_record.accommodation_address = session.accommodation_address
        vacation_record.itinerary_data = itinerary_data_payload
    else:
        vacation_record = models.Vacation(
            user_id=token.sub,
            session_id=session.id,
            destination=session.destination or "TBD Plan",
            origin=session.departure,
            from_date=session.from_date,
            to_date=session.to_date,
            adults=session.adults or 1,
            children=session.children or 0,
            flights_url=session.flights_url,
            flight_price=session.flight_price,
            flight_ccy=session.flight_ccy,
            airport_name=session.airport_name,
            accommodation_url=session.accommodation_url,
            accommodation_price=session.accommodation_price,
            accommodation_ccy=session.accommodation_ccy,
            accommodation_name=session.accommodation_name,
            accommodation_address=session.accommodation_address,
            itinerary_data=itinerary_data_payload,
            is_finalized=False
        )
        db.add(vacation_record)

    try:
        await db.commit()
        return {
            "status": "success",
            "message": "Session compiled successfully.",
            "vacation_id": vacation_record.id,
            "itinerary_data": itinerary_data_payload
        }
    except Exception as commit_err:
        await db.rollback()
        log.error(f"Database transaction failure during compilation commit: {str(commit_err)}")
        raise HTTPException(status_code=500, detail="Database write error during validation pass")

async def process_email_and_notify(user_id: str, email_to: str, vacation_payload: dict):
    """
    Runs out-of-band in background workers: Generates and dispatches the travel PDF, 
    then commits a real-time system notification indicating status.
    """
    destination = vacation_payload.get("destination", "your destination")
    try:
        success = await send_vacation_blueprint_email(email_to, vacation_payload)
        
        async for db in get_db():
            if success:
                db.add(models.Notification(
                    user_id=user_id,
                    category="EMAIL_SUCCESS",
                    message=f"🎉 Pack your bags! Your detailed TuRAG Blueprint for {destination} is waiting in your inbox."
                ))
            else:
                db.add(models.Notification(
                    user_id=user_id,
                    category="EMAIL_ERROR",
                    message=f"✈️ Slight turbulence: We couldn't deliver your {destination} itinerary email. You can still access it anytime from your dashboard."
                ))
            await db.commit()
            break
            
    except Exception as e:
        log.error(f"Background serialization or mailing runner failure: {str(e)}", exc_info=True)
        async for db in get_db():
            db.add(models.Notification(
                user_id=user_id,
                category="EMAIL_ERROR",
                message=f"⚠️ Internal network variance occurred while finalizing your trip to {destination}. Your data is safely stored in your travel passport log!"
            ))
            await db.commit()
            break

@router.post("/finalize/{session_id}")
async def finalize_and_email_session(
    session_id: int,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db), 
    token: TokenPayload = Depends(access_token_header)
):
    """
    Finalizes a vacation sequence: Locks dynamic edits, activates long-term travel 
    history visibility flags, and queues automated PDF documentation dispatches.
    """
    vacation_stmt = select(models.Vacation).where(
        models.Vacation.session_id == session_id,
        models.Vacation.user_id == token.sub
    )
    vacation = (await db.execute(vacation_stmt)).scalar_one_or_none()
    
    if not vacation:
        raise HTTPException(
            status_code=404, 
            detail="Compiled itinerary snapshot not found. Please compile the session state matrices first."
        )

    user_stmt = select(models.User).where(models.User.id == token.sub)
    user = (await db.execute(user_stmt)).scalar_one_or_none()
    
    if not user or not user.email:
        raise HTTPException(status_code=400, detail="Authenticated profile lacks a valid communication routing address.")

    session_stmt = select(models.VacationSession).where(models.VacationSession.id == session_id)
    session = (await db.execute(session_stmt)).scalar_one_or_none()

    vacation.is_finalized = True
    
    if session:
        session.is_active = False

    vacation_payload = {
        "id": vacation.id,
        "destination": vacation.destination,
        "origin": vacation.origin,
        "from_date": vacation.from_date.isoformat() if vacation.from_date else None,
        "to_date": vacation.to_date.isoformat() if vacation.to_date else None,
        "adults": vacation.adults,
        "children": vacation.children,
        "flight_price": vacation.flight_price,
        "flight_ccy": vacation.flight_ccy,
        "airport_name": vacation.airport_name,
        "flights_url": vacation.flights_url,
        "accommodation_price": vacation.accommodation_price,
        "accommodation_ccy": vacation.accommodation_ccy,
        "accommodation_name": vacation.accommodation_name,
        "accommodation_address": vacation.accommodation_address,
        "accommodation_url": vacation.accommodation_url,
        "itinerary_data": vacation.itinerary_data
    }

    try:
        await db.commit()
    except Exception as commit_err:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Database state transaction failure: {str(commit_err)}")

    background_tasks.add_task(
        process_email_and_notify, 
        user_id=token.sub, 
        email_to=user.email, 
        vacation_payload=vacation_payload
    )

    return {
        "status": "success",
        "message": "Itinerary locked successfully. Electronic document delivery manifest initialized.",
        "vacation_id": vacation.id
    }

@router.delete("/{session_id}")
async def delete_vacation_session(
    session_id: int,
    db: AsyncSession = Depends(get_db),
    access_token: TokenPayload = Depends(access_token_header)
    ):
    """Delete an existing vacation session for the authenticated user."""
    log.info(f"Deleting vacation session {session_id} for user: {access_token.sub}")
    try:
        stmt = delete(models.VacationSession).filter_by(
            id=session_id, user_id=access_token.sub
        )
        await db.execute(stmt)
        await db.commit()
        log.info(f"Vacation session {session_id} deleted successfully.")
    except Exception as e:
        await db.rollback()
        log.error(f"Error deleting vacation session {session_id}: {e}")
        raise HTTPException(status_code=500, detail="Error deleting vacation session")
    return {"detail": "Vacation session deleted successfully"}

@router.get("/{session_id}")
async def get_vacation_session(
    session_id: int,
    db: AsyncSession = Depends(get_db),
    access_token: TokenPayload = Depends(access_token_header)
    ):
    """Retrieve details of a vacation session for the authenticated user."""
    log.info(f"Retrieving vacation session {session_id} for user: {access_token.sub}")
    stmt = select(models.VacationSession).filter_by(
        id=session_id, user_id=access_token.sub
    )
    result = await db.execute(stmt)
    session = result.scalars().first()
    if not session:
        log.warning(f"Vacation session {session_id} not found for user: {access_token.sub}")
        raise HTTPException(status_code=404, detail="Vacation session not found")
    return session

