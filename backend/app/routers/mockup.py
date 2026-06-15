"""Authentication router using AuthX."""
import asyncio
import json

from authx import TokenPayload
from fastapi import APIRouter, Depends, HTTPException, Request, Response, BackgroundTasks
from fastapi.responses import StreamingResponse
import jwt
from pydantic import BaseModel
from app.core.auth import auth, refresh_token_cookie, access_token_header
from app.core.database import get_checkpointer, get_db
from app import models, schemas, utils
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timezone
from app.core.config import settings
from app.core.cache import redis_cache

router = APIRouter(prefix="/mock", tags=["MockUp"])

@router.post("/refresh")
async def refresh_token(
    response: Response,
    token: TokenPayload = Depends(access_token_header),
    db: AsyncSession = Depends(get_db)
):
    try:    
        new_access = auth.create_access_token(uid=token.sub)
        new_refresh_str = auth.create_refresh_token(uid=token.sub)

        payload = jwt.decode(new_refresh_str, options={"verify_signature": False})
        
        refresh_jti = payload.get("jti")
        refresh_exp = payload.get("exp")

        expiry_datetime = datetime.fromtimestamp(refresh_exp, tz=timezone.utc)

        await utils.security.blacklist_token(
            db=db, 
            token=refresh_jti, 
            expires_at=expiry_datetime
        )

        auth.unset_cookies(response)
        auth.set_refresh_cookies(new_refresh_str, response)

        return {
            "access_token": new_access,
        }
    except Exception as e:
        print(f"Error in refresh_token: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Eroare interna in mock: {str(e)}")
    

MOCK_TOURISM_DATA = {
    "flights": [
        {"id": 101, "airline": "Wizz Air", "departure": "OTP", "arrival": "FCO", "price_eur": 89.99},
        {"id": 102, "airline": "Ryanair", "departure": "OTP", "arrival": "CIA", "price_eur": 64.50}
    ],
    "hotels": [
        {"id": 201, "name": "Hotel Navona Roma", "stars": 3, "price_per_night_eur": 110},
        {"id": 202, "name": "Radisson Blu GHR", "stars": 5, "price_per_night_eur": 240}
    ]
}

@redis_cache(expire_time=900)
async def fetch_live_offers_simulation(session_id: int = None):

    await asyncio.sleep(5.0)
    return MOCK_TOURISM_DATA

@router.get("/offers/{session_id}")
async def get_mock_offers(session_id: int):
    """
    Ruta protejata prin cache. Primul apel va rula fetch_live_offers_simulation,
    urmatoarele vor fi servite direct din memoria RAM de catre Redis.
    """
    result = await fetch_live_offers_simulation(session_id=session_id)
    return result


async def sse_discovery_generator(session_id: int):
    """
    Generator asincron care simulează cele 3 evenimente din graful LangGraph.
    Folosește mici pauze asincrone pentru a mima procesarea reală a nodurilor.
    """
    try:
        await asyncio.sleep(2.0)
        event1 = {
            "node": "Information_collector",
            "status": "extracting",
            "data": {"destination": "Paris", "duration_days": 4}
        }
        yield f"event: update\ndata: {json.dumps(event1)}\n\n"
        await asyncio.sleep(0.1)

        event2 = {
            "node": "db_validator",
            "status": "persisted",
            "session_id": session_id,
            "is_complete": True
        }
        yield f"event: update\ndata: {json.dumps(event2)}\n\n"


        await asyncio.sleep(3.0)

        event3 = {
            "node": "responder",
            "status": "finished",
            "response": "Am salvat detaliile pentru Paris. Trecem la pasul următor!"
        }
        yield f"event: update\ndata: {json.dumps(event3)}\n\n"

    except asyncio.CancelledError:
        pass

@router.get("/discovery/stream/{session_id}")
async def stream_discovery(
    session_id: int,
):
    """
    Endpoint de streaming SSE protejat. Măsoară capacitatea serverului
    de a menține conexiuni HTTP deschise sub încărcare concurentă.
    """
    return StreamingResponse(
        sse_discovery_generator(session_id), 
        media_type="text/event-stream"
    )