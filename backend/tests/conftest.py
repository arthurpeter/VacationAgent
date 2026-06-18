import pytest
from unittest.mock import AsyncMock
from app.core.database import langgraph_pool


@pytest.fixture(scope="session", autouse=True)
def mock_global_langgraph_pool():
    """
    Dezactiveaza deschiderea si inchiderea reala a pool-ului psycopg pentru LangGraph.
    Previne eroarea OperationalError cauzata de ciclurile repetitive de startup/shutdown din FastAPI.
    """
    langgraph_pool.open = AsyncMock()
    langgraph_pool.close = AsyncMock()
