import os
import sys
# Add the src directory to Python path for relative imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI, HTTPException, Request
import uvicorn
from routers import auth
from agents.utils import *
from agents.agent import Agent

app = FastAPI(
    title="Vacation Agent API",
    description="API for vacation planning agent with authentication",
    version="1.0.0"
)

# Include routers
app.include_router(auth.router)

agent = Agent()


@app.post("/payload-template")
async def payload_template(payload: Request):
    try:
        data = await payload.json()
        return agent.do_stuff()

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/no-payload-template")
def no_payload_template():
    try:
        return agent.do_stuff()

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health", tags=["Health"])
def healthcheck():
    return {"status": "ok"}

if __name__ == "__main__":
    debug_mode = os.getenv("DEBUG", "false").lower() == "true"
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=5000,
        reload=debug_mode,  # Automatically reloads code if debug is on
        log_level="debug" if debug_mode else "info"
    )