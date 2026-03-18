from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base
from psycopg_pool import AsyncConnectionPool
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from app.core.config import settings
from app.core.logger import get_logger

log = get_logger(__name__)

safe_max_connections = max(1, settings.DB_MAX_CONNECTIONS - 10)
pool_size_per_worker = max(1, safe_max_connections // settings.WORKER_COUNT)

lg_pool_size = max(1, min(3, int(pool_size_per_worker * 0.2)))

app_pool_size = max(1, pool_size_per_worker - lg_pool_size)

engine = create_async_engine(
    settings.DATABASE_URL,
    pool_size=app_pool_size,
    max_overflow=int(app_pool_size * 0.2),
    pool_pre_ping=True,
    pool_recycle=3600
)

log.info(
    f"Connected to async PostgreSQL. Worker Pool Limit: {pool_size_per_worker} "
    f"(App ORM: {app_pool_size}, LangGraph: {lg_pool_size})"
)

SessionLocal = async_sessionmaker(
    autocommit=False, 
    autoflush=False, 
    bind=engine, 
    class_=AsyncSession,
    expire_on_commit=False
)

SessionLocal = async_sessionmaker(
    autocommit=False, 
    autoflush=False, 
    bind=engine, 
    class_=AsyncSession,
    expire_on_commit=False
)

Base = declarative_base()

raw_db_url = settings.DATABASE_URL.replace("+asyncpg", "").replace("+psycopg", "")

langgraph_pool = AsyncConnectionPool(
    conninfo=raw_db_url,
    min_size=1,
    max_size=lg_pool_size,
    open=False
)

async def get_db():
    async with SessionLocal() as db:
        try:
            yield db
        finally:
            await db.close()

async def get_checkpointer():
    """New: Yields the configured LangGraph Checkpointer."""
    yield AsyncPostgresSaver(langgraph_pool)