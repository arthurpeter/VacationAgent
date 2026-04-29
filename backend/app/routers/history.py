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
from datetime import datetime
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from pydantic import BaseModel, ConfigDict


logger = get_logger(__name__)

router = APIRouter(prefix="/history", tags=["history"])

class VacationSummary(BaseModel):
    id: str
    destination: str
    origin: Optional[str] = None
    from_date: Optional[str] = None
    to_date: Optional[str] = None
    flight_price: Optional[float] = None
    flight_ccy: Optional[str] = None
    accomodation_price: Optional[float] = None
    accomodation_ccy: Optional[str] = None
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class VacationDetail(VacationSummary):
    people_count: Optional[int] = None
    itinerary_data: Optional[Any] = None
    transit_strategy: Optional[Any] = None

@router.get("/vacations", response_model=List[VacationSummary])
async def get_all_history(
    db: AsyncSession = Depends(get_db),
    token: TokenPayload = Depends(access_token_header)
):
    """
    Fetches the lightweight summary of all vacations for the grid view.
    Defers the heavy JSON columns to save bandwidth and DB memory.
    """
    stmt = select(models.Vacation).where(
        models.Vacation.user_id == token.sub
    ).order_by(
        models.Vacation.created_at.desc()
    ).options(
        defer(models.Vacation.itinerary_data),
        defer(models.Vacation.transit_strategy)
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