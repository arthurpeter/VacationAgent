from typing import Any, List, Optional

from app.core.database import get_checkpointer, get_db
from fastapi import APIRouter, Depends, HTTPException, Query
from app import schemas, models
from app.core.logger import get_logger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text, update
from sqlalchemy.orm import defer
from authx import TokenPayload
from app.core.auth import access_token_header
from datetime import date, datetime
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from pydantic import BaseModel, ConfigDict


logger = get_logger(__name__)

router = APIRouter(prefix="/history", tags=["history"])

class VacationSummary(BaseModel):
    """
    Lightweight Schema for the Dashboard Cards.
    Includes pricing and names so cards can render stats immediately,
    but completely drops heavy strings and giant JSON blocks.
    """
    id: str
    destination: str
    origin: Optional[str] = None
    from_date: Optional[date] = None
    to_date: Optional[date] = None
    adults: int = 1
    children: int = 0
    
    # Financial snapshots for quick rendering
    flight_price: Optional[float] = None
    flight_ccy: Optional[str] = None
    airport_name: Optional[str] = None
    
    accommodation_price: Optional[float] = None
    accommodation_ccy: Optional[str] = None
    accommodation_name: Optional[str] = None
    
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class VacationDetail(VacationSummary):
    """
    Heavyweight Schema for the Full Detailed Document / Step 4 Overview.
    Inherits all metadata from Summary and appends the bulky actionable fields.
    """
    flights_url: Optional[str] = None
    accommodation_url: Optional[str] = None
    accommodation_address: Optional[str] = None
    itinerary_data: Optional[Any] = None

@router.get("/vacations", response_model=List[VacationSummary])
async def get_all_history(
    db: AsyncSession = Depends(get_db),
    token: TokenPayload = Depends(access_token_header)
):
    """
    Fetches lightweight summaries for the history card grids.
    Filters out active step-4 compiler drafts natively.
    """
    stmt = select(models.Vacation).where(
        models.Vacation.user_id == token.sub,
        models.Vacation.is_finalized == True
    ).order_by(
        models.Vacation.created_at.desc()
    ).options(
        defer(models.Vacation.flights_url),
        defer(models.Vacation.accommodation_url),
        defer(models.Vacation.accommodation_address),
        defer(models.Vacation.itinerary_data)
    )
    
    result = await db.execute(stmt)
    return result.scalars().all()

@router.get("/vacations/{vacation_id}", response_model=VacationDetail)
async def get_vacation_details(
    vacation_id: str,
    db: AsyncSession = Depends(get_db),
    token: TokenPayload = Depends(access_token_header)
):
    """
    Fetches the full, heavyweight vacation blueprint.
    """
    stmt = select(models.Vacation).where(
        models.Vacation.id == vacation_id,
        models.Vacation.user_id == token.sub
    )
    vacation = (await db.execute(stmt)).scalar_one_or_none()
    
    if not vacation:
        raise HTTPException(status_code=404, detail="Vacation not found")
        
    return vacation


@router.delete("/vacations/{vacation_id}")
async def delete_history(
    vacation_id: str,
    db: AsyncSession = Depends(get_db),
    token: TokenPayload = Depends(access_token_header)
):
    """
    Deletes a specific vacation history record permanently.
    """
    stmt = select(models.Vacation).where(
        models.Vacation.id == vacation_id,
        models.Vacation.user_id == token.sub
    )
    vacation = (await db.execute(stmt)).scalar_one_or_none()

    if not vacation:
        raise HTTPException(status_code=404, detail="Vacation history not found or unauthorized")

    await db.delete(vacation)
    await db.commit()

    return {"message": "Vacation passport deleted successfully"}