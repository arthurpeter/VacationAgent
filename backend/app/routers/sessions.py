from pydantic import BaseModel
from datetime import datetime
from app.schemas.vacation import SessionDataUpdate
from app.core.database import get_db
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

