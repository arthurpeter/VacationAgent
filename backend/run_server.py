"""
Startup script for the Vacation Agent API
Run this from the backend directory: python run_server.py
"""
import sys
import os
import uvicorn

# Change to the directory containing this script
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Add app to Python path
app_path = os.path.join(os.path.dirname(__file__), 'app')
sys.path.insert(0, app_path)

if __name__ == "__main__":
    debug_mode = os.getenv("DEBUG", "false").lower() == "true"
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=5000,
        reload=debug_mode,
        log_level="debug" if debug_mode else "info"
    )
