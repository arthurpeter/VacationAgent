import pytest
from unittest.mock import AsyncMock, patch
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient
from authx import TokenPayload

from app.main import app
from app.core.database import get_db, Base
from app.models.user import User
from app.models.vacation_session import VacationSession
from app.core.auth import auth, refresh_token_cookie

DATABASE_URL = "sqlite:///:memory:"


class MockAsyncSession:
    def __init__(self, sync_session):
        self.sync_session = sync_session

    async def execute(self, statement, *args, **kwargs):
        return self.sync_session.execute(statement, *args, **kwargs)

    def add(self, instance, *args, **kwargs):
        return self.sync_session.add(instance, *args, **kwargs)

    async def delete(self, instance, *args, **kwargs):
        return self.sync_session.delete(instance, *args, **kwargs)

    async def refresh(self, instance, *args, **kwargs):
        return self.sync_session.refresh(instance, *args, **kwargs)

    async def commit(self):
        self.sync_session.commit()

    async def rollback(self):
        self.sync_session.rollback()

    async def close(self):
        pass


@pytest.fixture(name="db_session")
def fixture_db_session():
    engine = create_engine(
        DATABASE_URL, poolclass=StaticPool, connect_args={"check_same_thread": False}
    )
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()
    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)


@patch("app.routers.auth.send_verification_email")
@patch("app.routers.auth.decode_verification_token")
def test_user_registration_and_verification_flow(mock_decode, mock_send, db_session):
    mock_decode.return_value = "newuser@example.com"

    async def override_get_db():
        yield MockAsyncSession(db_session)

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as client:
        register_payload = {
            "email": "newuser@example.com",
            "password": "SecurePassword123!",
            "confirm_password": "SecurePassword123!",
        }
        reg_response = client.post("/auth/register", json=register_payload)
        assert reg_response.status_code == 200

        stmt = select(User).where(User.email == "newuser@example.com")
        db_user = db_session.execute(stmt).scalars().first()
        assert db_user is not None
        assert db_user.is_verified is False
        mock_send.assert_called_once_with("newuser@example.com")

        verify_response = client.post("/auth/verify-email?token=mock_token")
        assert verify_response.status_code == 200

        db_session.refresh(db_user)
        assert db_user.is_verified is True

        data = verify_response.json()
        assert "access_token" in data
        assert "refresh_token_cookie" in verify_response.cookies

    app.dependency_overrides.clear()


@patch("app.utils.security.blacklist_token", new_callable=AsyncMock)
def test_refresh_token_rotation(mock_blacklist, db_session):
    user = User(email="verified@example.com", hashed_password="pwd", is_verified=True)
    db_session.add(user)
    db_session.commit()

    async def override_get_db():
        yield MockAsyncSession(db_session)

    async def override_refresh_token_cookie():
        return TokenPayload(jti="mocked-refresh-jti", sub=str(user.id), exp=1784237094)

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[refresh_token_cookie] = override_refresh_token_cookie

    with TestClient(app) as client:
        refresh_response = client.post("/auth/refresh")

        assert refresh_response.status_code == 200
        assert "access_token" in refresh_response.json()
        assert mock_blacklist.called is True

    app.dependency_overrides.clear()


def test_vacation_session_isolation(db_session):
    user_attacker = User(
        email="attacker@example.com", hashed_password="pwd", is_verified=True
    )
    user_victim = User(
        email="victim@example.com", hashed_password="pwd", is_verified=True
    )
    db_session.add_all([user_attacker, user_victim])
    db_session.commit()

    session_victim = VacationSession(user_id=user_victim.id)
    db_session.add(session_victim)
    db_session.commit()

    token_attacker = auth.create_access_token(uid=user_attacker.id)

    async def override_get_db():
        yield MockAsyncSession(db_session)

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as client:
        headers = {"Authorization": f"Bearer {token_attacker}"}

        get_response = client.get(f"/session/{session_victim.id}", headers=headers)
        assert get_response.status_code == 404
        assert get_response.json()["detail"] == "Vacation session not found"

        patch_payload = {"destination": "Maldives", "currency": "USD"}
        patch_response = client.patch(
            f"/session/{session_victim.id}/details", json=patch_payload, headers=headers
        )
        assert patch_response.status_code == 404
        assert patch_response.json()["detail"] == "Session not found"

    app.dependency_overrides.clear()
