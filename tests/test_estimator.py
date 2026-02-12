import os
from unittest.mock import patch

from app.models.inference import AppleInference


def test_estimator_upload_no_auth(client):
    """Guest mode: no auth required"""
    dummy_image = ("test.jpg", b"fake image bytes", "image/jpeg")

    with patch.object(AppleInference, "run_inference") as mock_inference:
        mock_inference.return_value = {
            "counts": {"healthy": 5, "damaged_apple": 2, "total": 7},
            "detections": {"boxes": [], "class_ids": [], "confidences": []}
        }

        response = client.post(
            "/api/v1/estimator/estimate",
            files={"file": dummy_image}
        )

        assert response.status_code == 200
        data = response.json()
        assert "healthy_apples" in data
        assert data["healthy_apples"] == 5
        assert "damaged_apples" == 2


def test_estimator_missing_file(client):
    response = client.post("/api/v1/estimator/estimate")
    assert response.status_code == 422  # FastAPI validation error