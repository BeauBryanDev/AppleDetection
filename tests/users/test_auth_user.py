import pytest
from fastapi.testclient import TestClient

from seed_db import get_password_hash


def test_signup_new_user(client, db_session):
    payload = {
        "name": "New Farmer",
        "email": "newfarmer@example.com",
        "password": "securepass123",
        "phone_number": "+573001234567"
    }
    response = client.post("/api/v1/users/signup", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "newfarmer@example.com"
    assert "id" in data
    assert data["role"] == "farmer"


def test_signup_duplicate_email(client, test_user):
    payload = {
        "name": "Duplicate",
        "email": test_user.email,
        "password": "testpass123"
    }
    response = client.post("/api/v1/users/signup", json=payload)
    assert response.status_code == 400
    assert "Email is already in use" in response.json()["detail"]


def test_login_success(client, test_user, db_session):
    # Asegurarse que el usuario existe con password correcto
    test_user.password_hash = get_password_hash("correctpass123")
    db_session.commit()

    response = client.post(
        "/api/v1/auth/login",
        data={"username": test_user.email, "password": "correctpass123"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_wrong_password(client, test_user):
    response = client.post(
        "/api/v1/auth/login",
        data={"username": test_user.email, "password": "wrongpass"}
    )
    assert response.status_code == 401
    assert "Incorrect email or password" in response.json()["detail"]