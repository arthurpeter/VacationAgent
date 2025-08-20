"""
Main FastAPI application.
"""
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import Base, engine
from app.core.auth import auth
from app.core.jobs import start_jobs
from app.routers.auth import router as auth_router
from app.routers.users import router as users_router

# Create database tables using sync engine
Base.metadata.create_all(bind=engine)

# Start background jobs
start_jobs()

# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    debug=settings.DEBUG
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router)
app.include_router(users_router)

# Configure AuthX error handling
auth.handle_errors(app)


@app.get("/health", tags=["Health"])
def healthcheck():
    """Health check endpoint."""
    return {"status": "ok", "version": settings.VERSION}


