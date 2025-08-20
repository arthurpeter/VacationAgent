from apscheduler.schedulers.background import BackgroundScheduler
from app.utils.security import cleanup_blacklist

def start_jobs():
    scheduler = BackgroundScheduler()
    scheduler.add_job(cleanup_blacklist, 'interval', hours=1)
    scheduler.start()