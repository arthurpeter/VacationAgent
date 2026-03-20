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

from app.services.agents.discovery_graph import stream_discovery_message


log = get_logger(__name__)

router = APIRouter(prefix="/chat", tags=["Chat"])

class ChatRequest(BaseModel):
    message: str

@router.post("/discovery/{session_id}")
async def chat_discovery(
    session_id: int,
    request: ChatRequest,
    db: AsyncSession = Depends(get_db),
    checkpointer: AsyncPostgresSaver = Depends(get_checkpointer),
    # token: TokenPayload = Depends(access_token_header)
):
    # stmt = select(models.VacationSession).where(
    #     models.VacationSession.id == session_id,
    #     models.VacationSession.user_id == token.sub
    # )
    # result = await db.execute(stmt)
    # session = result.scalar_one_or_none()

    # if not session:
    #     log.warning(f"Unauthorized access attempt to session {session_id} by user {token.sub}")
    #     raise HTTPException(status_code=404, detail="Session not found")
    
    # log.info(f"User {token.sub} initiated discovery chat for session {session_id}")
    
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
    thread_id = str(session_id)
    
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
# --header 'Content-Type: application/json' \
# --data '{"message": "We will buy a seat for the 1 year old to sit on the plane"}'