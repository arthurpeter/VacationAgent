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
from langchain_core.messages import HumanMessage, AIMessage
from app.services.agents.itinerary_graph import generate_graph as generate_itinerary_graph, run_itinerary_graph
from app.schemas.itinerary import *
from app.services.agents.mobility_strategies import MobilityConfig




log = get_logger(__name__)

router = APIRouter(prefix="/itinerary", tags=["Itinerary"])

@router.post("/update-stage")
async def update_stage(
    data: UpdateStageRequest,
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
        raise HTTPException(status_code=404, detail="Session not found")

    graph = generate_itinerary_graph(checkpointer)
    config = {"configurable": {"thread_id": f"itinerary_{data.session_id}"}}
    
    await graph.aupdate_state(config, {"stage": data.stage})

    return {"status": "success", "new_stage": data.stage}

@router.post("/update-search-location")
async def update_search_location(
    data: UpdateSearchLocationRequest,
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
    current_state.values["search_location"] = data.new_location
    await graph.aupdate_state(config, {"search_location": data.new_location})

    return {"status": "success", "new_search_location": data.new_location}

@router.get("/state/{session_id}")
async def get_itinerary_state(
    session_id: int,
    db: AsyncSession = Depends(get_db),
    checkpointer: AsyncPostgresSaver = Depends(get_checkpointer),
    token: TokenPayload = Depends(access_token_header)
):
    stmt = select(models.VacationSession).where(
        models.VacationSession.id == session_id,
        models.VacationSession.user_id == token.sub
    )
    result = await db.execute(stmt)
    session = result.scalar_one_or_none()

    if not session:
        log.warning(f"Unauthorized access attempt to session {session_id} by user {token.sub}")
        raise HTTPException(status_code=404, detail="Session not found")
    config = {"configurable": {"thread_id": f"itinerary_{session_id}"}}
    
    graph = generate_itinerary_graph(checkpointer) 
    state = await graph.aget_state(config)
    
    if not state.values:
        return {
            "stage": 0,
            "pois": [],
            "resolved_attractions": [],
            "search_location": session.destination,
            "mobility_config": None,
        }
    
    ui_keys = {
        "stage", "pois", "resolved_attractions", "search_location", "mobility_config"
    }
    
    return {k: v for k, v in state.values.items() if k in ui_keys}

@router.post("/attractions/add-to-bucket")
async def add_to_bucket(
    data: AddToBucketRequest,
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

    new_poi = {"id": data.attraction_id, "bucket": data.bucket, "time_to_spend": data.time_to_spend, "name": data.name, "image_url": data.image_url, "location": data.location}
    updated_pois = [p for p in pois if p['id'] != data.attraction_id] + [new_poi]

    await graph.aupdate_state(config, {"pois": updated_pois})
    
    return {"status": "success", "pois": updated_pois}

@router.post("/attractions/search")
async def trigger_search(
    data: SearchAttractionsRequest,
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
    try:
        final_state = await run_itinerary_graph(
            session_id=data.session_id,
            action=data.action,
            stage=0,
            query=data.query,
            db=db,
            checkpointer=checkpointer
        )

        return {"resolved_attractions": final_state.get("resolved_attractions", [])}
    except Exception as e:
        log.error(f"Itinerary graph error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal processing error")

@router.post("/update-mobility")
async def update_mobility(
    data: UpdateMobilityRequest,
    db: AsyncSession = Depends(get_db),
    checkpointer: AsyncPostgresSaver = Depends(get_checkpointer),
    token: TokenPayload = Depends(access_token_header)
):
    stmt = select(models.VacationSession).where(
        models.VacationSession.id == data.session_id,
        models.VacationSession.user_id == token.sub
    )
    result = await db.execute(stmt)
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Session not found")

    graph = generate_itinerary_graph(checkpointer)
    config = {"configurable": {"thread_id": f"itinerary_{data.session_id}"}}
        
    validated_config = MobilityConfig.model_validate(data.config)
    
    await graph.aupdate_state(
        config, 
        {"mobility_config": validated_config.model_dump(mode='json')}
    )

    return {"status": "success"} 
    
@router.post("/logistics/transport")
async def trigger_public_transport_search(
    data: TransportRequest,
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
        log.warning(f"Unauthorized logistics access: {data.session_id} by user {token.sub}")
        raise HTTPException(status_code=404, detail="Session not found")

    try:
        final_state = await run_itinerary_graph(
            session_id=data.session_id,
            action=data.action,
            stage=1,
            query="",
            db=db,
            checkpointer=checkpointer
        )

        return {
            "status": "success", 
            "mobility_config": final_state.get("mobility_config")
        }

    except Exception as e:
        log.error(f"Transit research failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal AI processing error")
