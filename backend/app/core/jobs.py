from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timezone

from app.core.database import SessionLocal
from app.models.vacation_session import VacationSession
from app.models.blacklist_token import BlacklistToken
from logger import get_logger

log = get_logger(__name__)

def cleanup_blacklist():
    db = SessionLocal()
    try:
        now = datetime.now(timezone.utc)
        # perform set-based delete to avoid loading ORM objects
        deleted = (
            db.query(BlacklistToken)
            .filter(
                BlacklistToken.expires_at != None,
                BlacklistToken.expires_at < now
            )
            .delete(synchronize_session=False)
        )
        db.commit()
        log.info(f"Deleted {deleted} expired blacklist tokens")
    except Exception:
        db.rollback()
        log.exception("Error occurred while cleaning up expired blacklist tokens")
    finally:
        db.close()

def cleanup_expired_sessions():
    db = SessionLocal()
    try:
        now = datetime.now(timezone.utc)
        # perform set-based delete to avoid loading ORM objects
        deleted = (
            db.query(VacationSession)
            .filter(
                VacationSession.expires_at != None,
                VacationSession.expires_at < now,
            )
            .delete(synchronize_session=False)
        )
        db.commit()
        log.info(f"Deleted {deleted} expired vacation sessions")
    except Exception:
        db.rollback()
        log.exception("Error occurred while cleaning up expired vacation sessions")
    finally:
        db.close()

def start_jobs():
    scheduler = BackgroundScheduler()
    scheduler.add_job(cleanup_blacklist, 'interval', hours=1)
    scheduler.add_job(cleanup_expired_sessions, 'interval', hours=1)
    scheduler.start()
    log.info("Background jobs started")