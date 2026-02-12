def test_create_orchard_authenticated(client, test_user, auth_headers):
    payload = {
        "name": "My First Orchard",
        "location": "Cúcuta, Norte de Santander",
        "n_trees": 120
    }
    response = client.post(
        "/api/v1/farming/orchards",
        json=payload,
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "My First Orchard"
    assert data["user_id"] == test_user.id