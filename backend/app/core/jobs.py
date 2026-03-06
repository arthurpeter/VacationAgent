from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timezone
import asyncio

from sqlalchemy import delete
from app.core.database import SessionLocal
from app.models.vacation_session import VacationSession
from app.models.blacklist_token import BlacklistToken
from app.core.logger import get_logger

log = get_logger(__name__)

async def _cleanup_blacklist_async():
    async with SessionLocal() as db:
        try:
            now = datetime.now(timezone.utc)
            stmt = delete(BlacklistToken).where(
                BlacklistToken.expires_at != None,
                BlacklistToken.expires_at < now
            )
            result = await db.execute(stmt)
            await db.commit()
            log.info(f"Deleted {result.rowcount} expired blacklist tokens")
        except Exception:
            await db.rollback()
            log.exception("Error occurred while cleaning up expired blacklist tokens")

def cleanup_blacklist():
   asyncio.run(_cleanup_blacklist_async())

async def _cleanup_expired_sessions_async():
    async with SessionLocal() as db:
        try:
            now = datetime.now(timezone.utc)
            stmt = delete(VacationSession).where(
                VacationSession.expires_at != None,
                VacationSession.expires_at < now,
            )
            result = await db.execute(stmt)
            await db.commit()
            log.info(f"Deleted {result.rowcount} expired vacation sessions")
        except Exception:
            await db.rollback()
            log.exception("Error occurred while cleaning up expired vacation sessions")

def cleanup_expired_sessions():
    asyncio.run(_cleanup_expired_sessions_async())

def start_jobs():
    scheduler = BackgroundScheduler()
    scheduler.add_job(cleanup_blacklist, 'interval', hours=1)
    scheduler.add_job(cleanup_expired_sessions, 'interval', hours=1)
    scheduler.start()
    log.info("Background jobs started")