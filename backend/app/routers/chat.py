from app.core.database import get_checkpointer, get_db
from fastapi import APIRouter, Depends, HTTPException, Query
from app import schemas, models
from app.core.logger import get_logger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text, update
from authx import TokenPayload
from app.core.auth import access_token_header
from datetime import datetime
from typing import Optional
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from pydantic import BaseModel
from fastapi.responses import StreamingResponse
from langchain_core.messages import HumanMessage, AIMessage
from app.services.agents.discovery_graph import generate_graph as generate_discovery_graph
from app.services.agents.itinerary_graph import generate_graph as generate_itinerary_graph
from app.services.agents.discovery_graph import stream_discovery_message
from app.services.agents.itinerary_graph import stream_itinerary_message


log = get_logger(__name__)

router = APIRouter(prefix="/chat", tags=["Chat"])

class ChatRequest(BaseModel):
    message: Optional[str] = None
    action: Optional[str] = None

@router.get("/discovery/messages/{session_id}")
async def get_discovery_messages(
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
    
    log.info(f"User {token.sub} requested discovery messages for session {session_id}")

    graph = generate_discovery_graph(checkpointer)
    config = {"configurable": {"thread_id": f"discovery_{session_id}"}}
    
    current_state = await graph.aget_state(config)
    
    if not current_state.values:
        return {"messages": []}
        
    raw_messages = current_state.values.get("messages", [])
    formatted_messages = []
    
    for msg in raw_messages:
        if isinstance(msg, HumanMessage):
            formatted_messages.append({
                "sender": "user", 
                "text": msg.content
            })
        elif isinstance(msg, AIMessage):
            if msg.content:
                text_content = msg.content
                if isinstance(text_content, list):
                    text_content = "".join([block.get("text", "") for block in text_content if isinstance(block, dict)])
                
                formatted_messages.append({
                    "sender": "ai", 
                    "text": text_content
                })
                
    return {"messages": formatted_messages}

@router.post("/discovery/{session_id}")
async def chat_discovery(
    session_id: int,
    request: ChatRequest,
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

    if not request.message:
        raise HTTPException(status_code=422, detail="Message is required.")
    
    log.info(f"User {token.sub} initiated discovery chat for session {session_id}")
    
    return StreamingResponse(
        stream_discovery_message(
            session_id=session_id,
            user_message=request.message,
            db=db,
            checkpointer=checkpointer
        ),
        media_type="text/event-stream"
    )

# curl --location 'http://127.0.0.1:5000/chat/discovery/1' \
# --header 'Content-Type: application/json' \
# --data '{"message": "We will buy a seat for the 1 year old to sit on the plane"}'

@router.delete("/discovery/{session_id}")
async def reset_discovery_chat(
    session_id: int,
    db: AsyncSession = Depends(get_db),
):   
    thread_id = f"discovery_{session_id}"
    
    await db.execute(
        text("DELETE FROM checkpoint_writes WHERE thread_id = :thread_id"), 
        {"thread_id": thread_id}
    )
    await db.execute(
        text("DELETE FROM checkpoint_blobs WHERE thread_id = :thread_id"), 
        {"thread_id": thread_id}
    )
    await db.execute(
        text("DELETE FROM checkpoints WHERE thread_id = :thread_id"), 
        {"thread_id": thread_id}
    )
    
    await db.commit()
    
    log.info(f"Successfully wiped LangGraph memory for session {session_id}")
    
    return {"status": "success", "message": "Conversation memory wiped successfully."}

# curl --location --request DELETE 'http://127.0.0.1:5000/chat/discovery/1' \
# --header 'Content-Type: application/json'

@router.get("/itinerary/messages/{session_id}")
async def get_itinerary_messages(
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
    
    log.info(f"User {token.sub} requested itinerary messages for session {session_id}")

    graph = generate_itinerary_graph(checkpointer)
    config = {"configurable": {"thread_id": f"itinerary_{session_id}"}}
    
    current_state = await graph.aget_state(config)
    
    if not current_state.values:
        return {
            "messages": [],
            "pois": [],
            "daily_themes": {},
            "daily_plans": {},
            "daily_links": {},
            "are_themes_confirmed": False,
            "transit_strategy": {}
        }
        
    raw_messages = current_state.values.get("messages", [])
    formatted_messages = []
    
    for msg in raw_messages:
        if isinstance(msg, HumanMessage):
            formatted_messages.append({
                "sender": "user", 
                "text": msg.content
            })
        elif isinstance(msg, AIMessage):
            if msg.content:
                text_content = msg.content
                if isinstance(text_content, list):
                    text_content = "".join([block.get("text", "") for block in text_content if isinstance(block, dict)])
                
                formatted_messages.append({
                    "sender": "ai", 
                    "text": text_content
                })
                
    daily_themes = current_state.values.get("daily_themes") or {}
    daily_plans = current_state.values.get("daily_plans") or {}
    daily_links = current_state.values.get("daily_links") or {}
    are_themes_confirmed = current_state.values.get("are_themes_confirmed", False)
    transit_strategy = current_state.values.get("transit_strategy", {})
    pois = current_state.values.get("pois") or []
            
    return {
        "messages": formatted_messages,
        "pois": pois,
        "daily_themes": daily_themes,
        "daily_plans": daily_plans,
        "daily_links": daily_links,
        "are_themes_confirmed": are_themes_confirmed,
        "transit_strategy": transit_strategy,
    }

@router.post("/itinerary/confirm_themes/{session_id}")
async def confirm_itinerary_themes(
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
    
    graph = generate_itinerary_graph(checkpointer)
    config = {"configurable": {"thread_id": f"itinerary_{session_id}"}}

    await graph.aupdate_state(
        config, 
        {"are_themes_confirmed": True}
    )

    log.info(f"Session {session_id} transitioned to Phase 2 (Detailing).")
    return {"status": "success", "message": "Itinerary themes confirmed."}

@router.post("/itinerary/{session_id}")
async def chat_itinerary(
    session_id: int,
    request: ChatRequest,
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

    if not request.message and not request.action:
        raise HTTPException(status_code=422, detail="Message or action is required.")
    
    log.info(f"User {token.sub} initiated itinerary chat for session {session_id}")
    
    return StreamingResponse(
        stream_itinerary_message(
            session_id=session_id,
            user_message=request.message,
            db=db,
            checkpointer=checkpointer,
            action=request.action
        ),
        media_type="text/event-stream"
    )

# curl --location 'http://127.0.0.1:5000/chat/itinerary/1' \
# --header 'Content-Type: application/json' \
# --data '{"message": "Generate a preliminary itinerary based on what we have discovered so far"}'

@router.delete("/itinerary/{session_id}")
async def reset_itinerary_chat(
    session_id: int,
    db: AsyncSession = Depends(get_db),
):   
    thread_id = f"itinerary_{session_id}"
    
    await db.execute(
        text("DELETE FROM checkpoint_writes WHERE thread_id = :thread_id"), 
        {"thread_id": thread_id}
    )
    await db.execute(
        text("DELETE FROM checkpoint_blobs WHERE thread_id = :thread_id"), 
        {"thread_id": thread_id}
    )
    await db.execute(
        text("DELETE FROM checkpoints WHERE thread_id = :thread_id"), 
        {"thread_id": thread_id}
    )
    
    await db.commit()
    
    log.info(f"Successfully wiped LangGraph memory for session {session_id}")
    
    return {"status": "success", "message": "Conversation memory wiped successfully."}

# curl --location --request DELETE 'http://127.0.0.1:5000/chat/itinerary/1' \
# --header 'Content-Type: application/json'
