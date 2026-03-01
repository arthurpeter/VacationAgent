from pydantic import BaseModel
from datetime import datetime
from app.schemas.vacation import SessionDataUpdate
from app.core.database import get_db
from fastapi import APIRouter, Depends, HTTPException
from app import schemas, models
from app.core.logger import get_logger
from sqlalchemy.orm import Session
from authx import TokenPayload
from app.core.auth import auth
from app.models.vacation_session import SessionStage


log = get_logger(__name__)

router = APIRouter(prefix="/session", tags=["Session Management"])


@router.patch("/{session_id}/details")
async def update_session_details(
    session_id: int,
    data: SessionDataUpdate,
    db: Session = Depends(get_db),
    access_token: TokenPayload = Depends(auth.access_token_required)
):
    """Auto-saves the user's form data as they type."""
    session = db.query(models.VacationSession).filter_by(
        id=session_id, user_id=access_token.sub
    ).first()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    update_data = data.model_dump(exclude_unset=True)
    
    fmt = "%Y-%m-%d"
    if "from_date" in update_data and update_data["from_date"]:
        update_data["from_date"] = datetime.strptime(update_data["from_date"], fmt)
    if "to_date" in update_data and update_data["to_date"]:
        update_data["to_date"] = datetime.strptime(update_data["to_date"], fmt)

    for key, value in update_data.items():
        setattr(session, key, value)

    db.commit()
    
    return {"status": "success", "message": "Session auto-saved"}

class StageUpdate(BaseModel):
    stage: SessionStage

@router.patch("/{session_id}/stage")
async def update_session_stage(
    session_id: int,
    update: StageUpdate,
    db: Session = Depends(get_db),
    access_token: TokenPayload = Depends(auth.access_token_required)
):
    """Updates the user's progress stage."""
    session = db.query(models.VacationSession).filter_by(
        id=session_id, user_id=access_token.sub
    ).first()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    session.current_stage = update.stage
    db.commit()
    
    return {"status": "success", "current_stage": session.current_stage}

@router.post("/create")
async def create_vacation_session(
    db: Session = Depends(get_db),
    access_token: TokenPayload = Depends(auth.access_token_required)
    ):
    """Create a new vacation session for the authenticated user."""
    log.info(f"Creating vacation session for user: {access_token.sub}")
    new_session = models.VacationSession(
        user_id=access_token.sub
    )
    db.add(new_session)
    db.commit()
    db.refresh(new_session)
    return {"session_id": new_session.id}

@router.post("/delete/{session_id}")
async def delete_vacation_session(
    session_id: str,
    db: Session = Depends(get_db),
    access_token: TokenPayload = Depends(auth.access_token_required)
    ):
    """Delete an existing vacation session for the authenticated user."""
    log.info(f"Deleting vacation session {session_id} for user: {access_token.sub}")
    try:
        db.query(models.VacationSession).filter_by(
            id=session_id, user_id=access_token.sub
            ).delete()
        db.commit()
        log.info(f"Vacation session {session_id} deleted successfully.")
    except Exception as e:
        db.rollback()
        log.error(f"Error deleting vacation session {session_id}: {e}")
        raise HTTPException(status_code=500, detail="Error deleting vacation session")
    return {"detail": "Vacation session deleted successfully"}

@router.get("/getSessions")
async def get_sessions(
    db: Session = Depends(get_db),
    access_token: TokenPayload = Depends(auth.access_token_required)
    ):
    """Retrieve all vacation sessions for the authenticated user."""
    log.info(f"Retrieving all vacation sessions for user: {access_token.sub}")
    sessions = db.query(models.VacationSession).filter_by(
        user_id=access_token.sub
        ).all()
    ids = [session.id for session in sessions]
    return {"session_ids": ids}

@router.get("/{session_id}")
async def get_vacation_session(
    session_id: str,
    db: Session = Depends(get_db),
    access_token: TokenPayload = Depends(auth.access_token_required)
    ):
    """Retrieve details of a vacation session for the authenticated user."""
    log.info(f"Retrieving vacation session {session_id} for user: {access_token.sub}")
    session = db.query(models.VacationSession).filter_by(
        id=session_id, user_id=access_token.sub
        ).first()
    if not session:
        log.warning(f"Vacation session {session_id} not found for user: {access_token.sub}")
        raise HTTPException(status_code=404, detail="Vacation session not found")
    return session

