import asyncio
import orjson
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from sqlalchemy import select, update, or_
from app import models
from app.core.database import get_db
from app.core.auth import access_token_header, TokenPayload
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/notifications", tags=["Notifications"])

get_db_context = asynccontextmanager(get_db)

async def notification_stream_generator(user_id: str, request: Request):
    last_sent_hash = None
    last_abandon_check = datetime.min

    while True:
        if await request.is_disconnected():
            break

        async with get_db_context() as db:
            welcome_key = f"welcome_{user_id}"
            welcome_exists = await db.execute(select(models.Notification).where(models.Notification.event_key == welcome_key))
            
            if not welcome_exists.scalar():
                db.add(models.Notification(
                    user_id=user_id,
                    category="WELCOME",
                    event_key=welcome_key,
                    message="Welcome to TuRAG! 🌴 Start planning your next trip in the dashboard."
                ))
                await db.commit()

            if (datetime.now() - last_abandon_check).total_seconds() > 300:
                threshold = datetime.now() - timedelta(hours=24)
                sessions = await db.execute(select(models.VacationSession).where(
                    models.VacationSession.user_id == user_id,
                    models.VacationSession.updated_at < threshold,
                    models.VacationSession.is_active == True
                ))
                
                for session in sessions.scalars().all():
                    abandon_key = f"abandon_{session.id}"
                    exists = await db.execute(select(models.Notification).where(models.Notification.event_key == abandon_key))
                    
                    if not exists.scalar():
                        db.add(models.Notification(
                            user_id=user_id,
                            category="SESSION_ALERT",
                            event_key=abandon_key,
                            message=f"Still thinking about {session.destination or 'your trip'}? Jump back in!"
                        ))
                        
                await db.commit()
                last_abandon_check = datetime.now()

            result = await db.execute(select(models.Notification).where(
                models.Notification.user_id == user_id,
                models.Notification.deleted_at == None
            ).order_by(models.Notification.created_at.desc()))
            
            notifications = result.scalars().all()
            payload = [{
                "id": n.id,
                "category": n.category,
                "message": n.message,
                "is_read": n.is_read,
                "created_at": n.created_at.isoformat() if n.created_at else None
            } for n in notifications]

            current_hash = hash(orjson.dumps(payload))
            if current_hash != last_sent_hash:
                json_string = orjson.dumps(payload).decode("utf-8")
                yield f"data: {json_string}\n\n"
                last_sent_hash = current_hash

        await asyncio.sleep(60)

@router.get("/stream")
async def get_stream(request: Request, token=Depends(access_token_header)):
    return StreamingResponse(
        notification_stream_generator(token.sub, request),
        media_type="text/event-stream"
    )

@router.delete("/{notification_id}")
async def delete_notification(notification_id: int, db: AsyncSession = Depends(get_db), token = Depends(access_token_header)):
    await db.execute(
        update(models.Notification)
        .where(models.Notification.id == notification_id, models.Notification.user_id == token.sub)
        .values(deleted_at=datetime.now())
    )
    await db.commit()
    return {"status": "hidden"}

@router.patch("/read")
async def mark_all_read(db: AsyncSession = Depends(get_db), token = Depends(access_token_header)):
    await db.execute(
        update(models.Notification)
        .where(models.Notification.user_id == token.sub, models.Notification.is_read == False)
        .values(is_read=True)
    )
    await db.commit()
    return {"status": "updated"}