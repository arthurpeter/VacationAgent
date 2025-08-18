import src.main
from fastapi import FastAPI, HTTPException, Request
import uvicorn
#from pydantic import BaseModel
from src.utils import *
from agent import Agent

app = FastAPI()
agent = Agent()

# class InputText(BaseModel):
#     text: str

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