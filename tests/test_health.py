def test_root_endpoint(client):
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "Welcome to Apple Yield Estimator API" in data["message"]
    assert "status" in data
    assert data["status"] == "healthy"


def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "service" in data
    assert data["service"] == "yield-estimator-api"