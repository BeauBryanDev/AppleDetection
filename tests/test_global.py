import pytest
from fastapi.testclient import TestClient


def test_health_check(client: TestClient):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_root_endpoint(client: TestClient):
    response = client.get("/")
    assert response.status_code == 200
    assert "Welcome to" in response.json()["message"]


@pytest.mark.asyncio
async def test_login_endpoint(client: TestClient, db_session):
    # Create a test user first (you would normally use a fixture for this)
    from app.db.models.users import User
    from app.core.security import get_password_hash

    test_user = User(
        name="Test User",
        email="test@example.com",
        password_hash=get_password_hash("testpassword123"),
        role="farmer"
    )
    db_session.add(test_user)
    db_session.commit()

    response = client.post(
        "/api/v1/auth/login",
        data={"username": "test@example.com", "password": "testpassword123"}
    )
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert response.json()["token_type"] == "bearer"