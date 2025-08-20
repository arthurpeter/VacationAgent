from apscheduler.schedulers.background import BackgroundScheduler
from app.utils.security import cleanup_blacklist
from app.core.database import SessionLocal

def start_jobs():
    scheduler = BackgroundScheduler()
    scheduler.add_job(run_cleanup, 'interval', hours=1)
    scheduler.start()

def run_cleanup():
    db = SessionLocal()
    cleanup_blacklist(db)
    db.close()