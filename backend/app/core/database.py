from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base
from app.core.config import settings
from app.core.logger import get_logger

log = get_logger(__name__)

safe_max_connections = max(1, settings.DB_MAX_CONNECTIONS - 10)
pool_size_per_worker = max(1, safe_max_connections // settings.WORKER_COUNT)

engine = create_async_engine(
    settings.DATABASE_URL,
    pool_size=pool_size_per_worker,
    max_overflow=int(pool_size_per_worker * 0.2),
    pool_pre_ping=True,
    pool_recycle=3600
)

log.info(f"Connected to async PostgreSQL database. Pool size per worker: {pool_size_per_worker}")

SessionLocal = async_sessionmaker(
    autocommit=False, 
    autoflush=False, 
    bind=engine, 
    class_=AsyncSession,
    expire_on_commit=False
)

Base = declarative_base()

async def get_db():
    async with SessionLocal() as db:
        try:
            yield db
        finally:
            await db.close()