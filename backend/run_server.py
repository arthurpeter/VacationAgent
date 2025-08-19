"""
Startup script for the Vacation Agent API
Run this from the backend directory: python run_server.py
"""
import sys
import os

# Add src to Python path
src_path = os.path.join(os.path.dirname(__file__), 'src')
sys.path.insert(0, src_path)

# Now import and run the app
from src.main import app
import uvicorn

if __name__ == "__main__":
    debug_mode = os.getenv("DEBUG", "false").lower() == "true"
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=5000,
        reload=debug_mode,
        log_level="debug" if debug_mode else "info"
    )
