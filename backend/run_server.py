"""
Startup script for the Vacation Agent API
Run this from the backend directory: python run_server.py
"""
import sys
import os
import uvicorn
import multiprocessing
from app.core.config import settings

# Change to the directory containing this script
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Add app to Python path
app_path = os.path.join(os.path.dirname(__file__), 'app')
sys.path.insert(0, app_path)



if __name__ == "__main__":
    debug_mode = settings.DEBUG
    worker_count = settings.WORKER_COUNT if not debug_mode else 1
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=5000,
        reload=debug_mode,
        workers=worker_count,
        log_level="debug" if debug_mode else "info"
    )
