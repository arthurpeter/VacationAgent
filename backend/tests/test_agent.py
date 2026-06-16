import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.checkpoint.memory import MemorySaver
from app.main import app
from app.core.database import get_db, get_checkpointer, Base
from app.models.user import User
from app.models.vacation_session import VacationSession
from app.core.auth import auth
from app.services.agents.discovery_graph import generate_graph as generate_discovery_graph

DATABASE_URL = "sqlite:///:memory:"

class MockAsyncSession:
    def __init__(self, sync_session):
        self.sync_session = sync_session

    async def execute(self, statement, *args, **kwargs):
        return self.sync_session.execute(statement, *args, **kwargs)

    async def commit(self):
        self.sync_session.commit()

    async def rollback(self):
        self.sync_session.rollback()

    async def close(self):
        pass

@pytest.fixture(name="db_session")
def fixture_db_session():
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()
    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)

@pytest.mark.anyio
async def test_agent_context_persistence_and_retrieval(db_session):
    user = User(email="agent_test@example.com", hashed_password="pwd", is_verified=True)
    db_session.add(user)
    db_session.commit()

    vacation_session = VacationSession(id=1, user_id=user.id)
    db_session.add(vacation_session)
    db_session.commit()

    token = auth.create_access_token(uid=user.id)

    memory_checkpointer = MemorySaver()
    config = {"configurable": {"thread_id": "discovery_1"}}
    
    graph = generate_discovery_graph(memory_checkpointer)
    await graph.aupdate_state(
        config,
        {
            "messages": [
                HumanMessage(content="Vreau o vacanta de 5 zile in Roma"),
                AIMessage(content="Ce buget ai alocat pentru zbor si cazare?")
            ]
        }
    )

    async def override_get_db():
        yield MockAsyncSession(db_session)

    async def override_get_checkpointer():
        yield memory_checkpointer

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_checkpointer] = override_get_checkpointer

    with TestClient(app) as client:
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/chat/discovery/messages/1", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "messages" in data
        assert len(data["messages"]) == 2
        assert data["messages"][0]["sender"] == "user"
        assert data["messages"][0]["text"] == "Vreau o vacanta de 5 zile in Roma"
        assert data["messages"][1]["sender"] == "ai"
        assert data["messages"][1]["text"] == "Ce buget ai alocat pentru zbor si cazare?"

    app.dependency_overrides.clear()