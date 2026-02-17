import os
from unittest.mock import patch

from app.models.inference import AppleInference


def test_estimator_upload_no_auth(client):
    """Guest mode: no auth required"""
    dummy_image = ("test.jpg", b"fake image bytes", "image/jpeg")

    with patch.object(AppleInference, "run_inference") as mock_inference:
        mock_inference.return_value = {
            "counts": {"healthy": 5, "damaged_apple": 2, "total": 7, "red_apple": 5, "green_apple": 0},
            "detections": {"boxes": [], "class_ids": [], "confidences": []}
        }
    
        with patch("app.api.v1.endpoints.estimator.draw_cyberpunk_detections") as mock_draw:
            mock_draw.return_value = b"fake_processed_image"

            response = client.post(
                "/api/v1/estimator/estimate",
                files={"file": dummy_image}
            )

        assert response.status_code == 200
        # The endpoint returns an image, not JSON. Data is in headers.
        assert "X-Healthy-Count" in response.headers
        assert response.headers["X-Healthy-Count"] == "5"
        assert response.headers["X-Damaged-Count"] == "2"


def test_estimator_missing_file(client):
    response = client.post("/api/v1/estimator/estimate")
    assert response.status_code == 422  # FastAPI validation error