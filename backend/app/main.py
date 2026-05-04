"""
Main FastAPI application.
"""
from app.core.logger import configure_logging
configure_logging()

from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import Base, engine, langgraph_pool
from app.core.auth import auth

from app.routers.auth import router as auth_router
from app.routers.users import router as users_router
from app.routers.sessions import router as sessions_router
from app.routers.search import router as search_router
from app.routers.chat import router as chat_router
from app.routers.itinerary import router as itinerary_router
from app.routers.notifications import router as notifications_router
from app.routers.history import router as history_router
from app.core.logger import get_logger

log = get_logger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    await langgraph_pool.open()
    log.info("LangGraph checkpointer pool opened.")
    
    yield
    
    await langgraph_pool.close()
    log.info("LangGraph checkpointer pool closed.")

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    debug=settings.DEBUG,
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(users_router)
app.include_router(sessions_router)
app.include_router(search_router)
app.include_router(chat_router)
app.include_router(itinerary_router)
app.include_router(notifications_router)
app.include_router(history_router)
auth.handle_errors(app)


@app.get("/health", tags=["Health"])
def healthcheck():
    """Health check endpoint."""
    return {"status": "ok", "version": settings.VERSION}

