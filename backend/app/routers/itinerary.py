from app.core.database import get_checkpointer, get_db
from fastapi import APIRouter, Depends, HTTPException, Query
from app import schemas, models
from app.core.logger import get_logger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text, update
from authx import TokenPayload
from app.core.auth import access_token_header
from datetime import datetime
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from pydantic import BaseModel
from fastapi.responses import StreamingResponse
from langchain_core.messages import HumanMessage, AIMessage
from app.services.agents.itinerary_graph import generate_graph as generate_itinerary_graph



log = get_logger(__name__)

router = APIRouter(prefix="/itinerary", tags=["Itinerary"])

@router.post("/attractions/add-to-bucket")
async def add_to_bucket(
    data: schemas.AddToBucketRequest,
    db: AsyncSession = Depends(get_db),
    checkpointer: AsyncPostgresSaver = Depends(get_checkpointer),
    token: TokenPayload = Depends(access_token_header)
):
    stmt = select(models.VacationSession).where(
        models.VacationSession.id == data.session_id,
        models.VacationSession.user_id == token.sub
    )
    result = await db.execute(stmt)
    session = result.scalar_one_or_none()

    if not session:
        log.warning(f"Unauthorized access attempt to session {data.session_id} by user {token.sub}")
        raise HTTPException(status_code=404, detail="Session not found")


    graph = generate_itinerary_graph(checkpointer)
    config = {"configurable": {"thread_id": f"itinerary_{data.session_id}"}}

    current_state = await graph.aget_state(config)

    pois = current_state.values.get("pois", [])

    new_poi = {"id": data.attraction_id, "bucket": data.bucket, "time_to_spend": data.time_to_spend}
    updated_pois = [p for p in pois if p['id'] != data.attraction_id] + [new_poi]

    await graph.aupdate_state(config, {"pois": updated_pois})
    
    return {"status": "success", "pois": updated_pois}

@router.post("/attractions/search")
async def trigger_search(
    data: schemas.SearchAttractionsRequest,
    db: AsyncSession = Depends(get_db),
    checkpointer: AsyncPostgresSaver = Depends(get_checkpointer),
    token: TokenPayload = Depends(access_token_header)
):
    stmt = select(models.VacationSession).where(
        models.VacationSession.id == data.session_id,
        models.VacationSession.user_id == token.sub
    )
    result = await db.execute(stmt)
    session = result.scalar_one_or_none()

    if not session:
        log.warning(f"Unauthorized access attempt to session {data.session_id} by user {token.sub}")
        raise HTTPException(status_code=404, detail="Session not found")
    
    

