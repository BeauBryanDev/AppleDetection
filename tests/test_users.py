def test_read_me_authenticated(client, test_user, auth_headers):
    response = client.get("/api/v1/users/me", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == test_user.email
    assert data["name"] == test_user.name


def test_update_own_profile(client, test_user, auth_headers):
    payload = {"name": "Updated Farmer", "phone_number": "+573009876543"}
    response = client.patch(
        f"/api/v1/users/{test_user.id}",
        json=payload,
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Farmer"
    assert data["phone_number"] == "+573009876543"


def test_cannot_update_other_user(client, test_user, auth_headers):
    other_user_id = 999  # ID que no existe o pertenece a otro
    payload = {"name": "Hacked"}
    response = client.patch(
        f"/api/v1/users/{other_user_id}",
        json=payload,
        headers=auth_headers
    )
    assert response.status_code == 403
    assert "do not have permission" in response.json()["detail"]