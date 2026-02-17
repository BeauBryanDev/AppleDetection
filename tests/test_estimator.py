import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.db.models.farming import YieldRecord, Image, Prediction, Detection
from app.db.models.users import User

from app.models.inference import AppleInference
from app.core.config import settings
from app.db.models.users import UserRole
from app.core import security
from datetime import datetime, timedelta, timezone
import jwt
import os

# Helper to create a JWT token for testing purposes.
def create_jwt_token(user_id: int, role: UserRole, expires_delta: timedelta = None) -> str:
    if expires_delta is None:
        expires_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    expire = datetime.now(timezone.utc) + expires_delta
    to_encode = {"sub": str(user_id), "role": role.value, "exp": expire}
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

# Dummy image for testing
DUMMY_IMAGE = ("test_image.jpg", b"fake_image_bytes", "image/jpeg")

# Mock inference results
MOCK_INFERENCE_RESULTS = {
    "counts": {"red_apple": 3, "green_apple": 2, "damaged_apple": 1, "total": 6},
    "detections": {
        "boxes": [[10, 10, 50, 50], [60, 60, 100, 100]],
        "class_ids": [0, 1], # 0 for apple, 1 for damaged_apple
        "confidences": [0.9, 0.8]
    }
}

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
        assert data["damaged_apples"] == 2


def test_estimator_missing_file(client):
    response = client.post("/api/v1/estimator/estimate")
    assert response.status_code == 422  # FastAPI validation error

# --- New Tests for /api/v1/estimator/estimate ---

@patch("app.api.v1.endpoints.estimator.draw_cyberpunk_detections")
@patch.object(AppleInference, "run_inference")
def test_estimator_authenticated_preview_mode(
    mock_run_inference: MagicMock,
    mock_draw_detections: MagicMock,
    client: TestClient,
    db_session: Session,
    auth_headers: dict,
    test_orchard,
    test_tree
):
    """
    Tests /api/v1/estimator/estimate for an authenticated user in preview mode.
    Ensures correct response and no database changes.
    """
    mock_run_inference.return_value = MOCK_INFERENCE_RESULTS
    mock_draw_detections.return_value = b"processed_image_bytes"

    # Verify initial database state
    assert db_session.query(YieldRecord).count() == 0
    assert db_session.query(Image).count() == 0
    assert db_session.query(Prediction).count() == 0
    assert db_session.query(Detection).count() == 0

    response = client.post(
        "/api/v1/estimator/estimate",
        headers=auth_headers,
        params={
            "orchard_id": test_orchard.id,
            "tree_id": test_tree.id,
            "preview": True, # Explicitly set to True for this test
            "confidence_threshold": 0.6
        },
        files={"file": DUMMY_IMAGE}
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"
    assert response.content == b"processed_image_bytes"

    # Verify headers
    assert response.headers["X-Healthy-Count"] == "5" # red_apple + green_apple
    assert response.headers["X-Damaged-Count"] == "1"
    assert response.headers["X-Total-Count"] == "6"
    health_idx = round((5 / 6) * 100, 2)
    assert response.headers["X-Health-Index"] == str(health_idx)
    assert response.headers["X-Record-ID"] == "None" # Should not be saved
    assert response.headers["X-Prediction-ID"] == "None" # Should not be saved
    assert response.headers["X-Preview-Mode"] == "true"
    assert response.headers["X-Mode"] == "authenticated"
    assert response.headers["X-Orchard-ID"] == str(test_orchard.id)
    assert response.headers["X-Tree-ID"] == str(test_tree.id)

    # Verify inference and drawing were called
    mock_run_inference.assert_called_once()
    assert mock_run_inference.call_args[0][0] == DUMMY_IMAGE[1] # raw image bytes
    assert mock_run_inference.call_args[0][1] == 0.64 * 0.6 # deep_confidence_threshold

    mock_draw_detections.assert_called_once()
    assert mock_draw_detections.call_args[0][0] == DUMMY_IMAGE[1] # original image bytes
    assert mock_draw_detections.call_args[0][1] == MOCK_INFERENCE_RESULTS["detections"]
    assert mock_draw_detections.call_args[0][2] == 0.85 * 0.6 # drawing threshold

    # Verify no new entries in the database
    assert db_session.query(YieldRecord).count() == 0
    assert db_session.query(Image).count() == 0
    assert db_session.query(Prediction).count() == 0
    assert db_session.query(Detection).count() == 0


@patch("app.api.v1.endpoints.estimator.draw_cyberpunk_detections")
@patch.object(AppleInference, "run_inference")
def test_estimator_authenticated_save_mode(
    mock_run_inference: MagicMock,
    mock_draw_detections: MagicMock,
    client: TestClient,
    db_session: Session,
    auth_headers: dict,
    test_user,
    test_orchard,
    test_tree
):
    """
    Tests /api/v1/estimator/estimate for an authenticated user in save mode (preview=False).
    Ensures correct response and that data is persisted in the database.
    """
    mock_run_inference.return_value = MOCK_INFERENCE_RESULTS
    mock_draw_detections.return_value = b"processed_image_bytes"

    # Verify initial database state
    assert db_session.query(YieldRecord).count() == 0
    assert db_session.query(Image).count() == 0
    assert db_session.query(Prediction).count() == 0
    assert db_session.query(Detection).count() == 0

    # Ensure 'uploads' directory exists for image saving
    if not os.path.exists("uploads"):
        os.makedirs("uploads")

    response = client.post(
        "/api/v1/estimator/estimate",
        headers=auth_headers,
        params={
            "orchard_id": test_orchard.id,
            "tree_id": test_tree.id,
            "preview": False, # Set to False for save mode
            "confidence_threshold": 0.5
        },
        files={"file": DUMMY_IMAGE}
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"
    assert response.content == b"processed_image_bytes"

    # Verify headers for saved data
    assert response.headers["X-Healthy-Count"] == "5"
    assert response.headers["X-Damaged-Count"] == "1"
    assert response.headers["X-Total-Count"] == "6"
    health_idx = round((5 / 6) * 100, 2)
    assert response.headers["X-Health-Index"] == str(health_idx)
    assert response.headers["X-Preview-Mode"] == "false"
    assert response.headers["X-Mode"] == "authenticated"
    assert response.headers["X-Orchard-ID"] == str(test_orchard.id)
    assert response.headers["X-Tree-ID"] == str(test_tree.id)
    assert response.headers["X-Record-ID"] != "None" # Should be saved
    assert response.headers["X-Prediction-ID"] != "None" # Should be saved

    # Verify new entries in the database
    assert db_session.query(YieldRecord).count() == 1
    assert db_session.query(Image).count() == 1
    assert db_session.query(Prediction).count() == 1
    assert db_session.query(Detection).count() == len(MOCK_INFERENCE_RESULTS["detections"]["boxes"])

    # Verify contents of saved records
    record = db_session.query(YieldRecord).first()
    assert record.user_id == test_user.id
    assert record.healthy_count == 5
    assert record.damaged_count == 1
    assert record.total_count == 6
    assert record.health_index == health_idx
    assert os.path.exists("uploads/" + record.filename) # Image should be saved to disk

    image = db_session.query(Image).first()
    assert image.user_id == test_user.id
    assert image.orchard_id == test_orchard.id
    assert image.tree_id == test_tree.id
    assert image.image_path == "uploads/" + record.filename # Should be the same filename

    prediction = db_session.query(Prediction).first()
    assert prediction.image_id == image.id
    assert prediction.total_apples == 6
    assert prediction.good_apples == 5
    assert prediction.damaged_apples == 1
    assert prediction.healthy_percentage == health_idx

    detections = db_session.query(Detection).all()
    assert len(detections) == 2
    assert detections[0].prediction_id == prediction.id
    assert detections[0].class_label == "apple" # class_id 0
    assert detections[1].class_label == "damaged_apple" # class_id 1
    # Clean up the created image file
    os.remove("uploads/" + record.filename)


@patch("app.api.v1.endpoints.estimator.validate_image_file")
@patch("app.api.v1.endpoints.estimator.draw_cyberpunk_detections")
@patch.object(AppleInference, "run_inference")
def test_estimator_auth_missing_orchard_id_param(
    mock_run_inference: MagicMock,
    mock_draw_detections: MagicMock,
    mock_validate_image_file: MagicMock,
    client: TestClient,
    auth_headers: dict,
    test_tree # tree needs an orchard, but we're testing missing orchard_id param
):
    """
    Tests /api/v1/estimator/estimate for an authenticated user missing orchard_id query parameter
    when tree_id is provided. Should return 400 Bad Request.
    """
    mock_run_inference.return_value = MOCK_INFERENCE_RESULTS
    mock_draw_detections.return_value = b"processed_image_bytes"
    mock_validate_image_file.return_value = None # Mock this to avoid file validation details

    response = client.post(
        "/api/v1/estimator/estimate",
        headers=auth_headers,
        params={
            # "orchard_id": test_orchard.id, # Missing
            "tree_id": test_tree.id,
            "preview": False
        },
        files={"file": DUMMY_IMAGE}
    )
    assert response.status_code == 400
    assert "detail" in response.json()
    assert "Tree ID cannot be provided without an Orchard ID" in response.json()["detail"]


@patch("app.api.v1.endpoints.estimator.draw_cyberpunk_detections")
@patch.object(AppleInference, "run_inference")
def test_estimator_auth_invalid_orchard_id(
    mock_run_inference: MagicMock,
    mock_draw_detections: MagicMock,
    client: TestClient,
    auth_headers: dict,
    test_tree # just for the tree_id
):
    """
    Tests /api/v1/estimator/estimate for an authenticated user with an invalid (non-existent) orchard_id.
    Should return 404 Not Found.
    """
    mock_run_inference.return_value = MOCK_INFERENCE_RESULTS
    mock_draw_detections.return_value = b"processed_image_bytes"

    response = client.post(
        "/api/v1/estimator/estimate",
        headers=auth_headers,
        params={
            "orchard_id": 99999, # Non-existent ID
            "tree_id": test_tree.id,
            "preview": False
        },
        files={"file": DUMMY_IMAGE}
    )
    assert response.status_code == 404
    assert "detail" in response.json()
    assert "Orchard 99999 not found" in response.json()["detail"]

@patch("app.api.v1.endpoints.estimator.draw_cyberpunk_detections")
@patch.object(AppleInference, "run_inference")
def test_estimator_auth_invalid_tree_id(
    mock_run_inference: MagicMock,
    mock_draw_detections: MagicMock,
    client: TestClient,
    auth_headers: dict,
    test_orchard
):
    """
    Tests /api/v1/estimator/estimate for an authenticated user with an invalid (non-existent) tree_id.
    Should return 404 Not Found.
    """
    mock_run_inference.return_value = MOCK_INFERENCE_RESULTS
    mock_draw_detections.return_value = b"processed_image_bytes"

    response = client.post(
        "/api/v1/estimator/estimate",
        headers=auth_headers,
        params={
            "orchard_id": test_orchard.id,
            "tree_id": 99999, # Non-existent ID
            "preview": False
        },
        files={"file": DUMMY_IMAGE}
    )
    assert response.status_code == 404
    assert "detail" in response.json()
    assert f"Tree 99999 not found in orchard {test_orchard.id}" in response.json()["detail"]

@patch("app.api.v1.endpoints.estimator.draw_cyberpunk_detections")
@patch.object(AppleInference, "run_inference")
def test_estimator_auth_unauthorized_orchard(
    mock_run_inference: MagicMock,
    mock_draw_detections: MagicMock,
    client: TestClient,
    auth_headers: dict,
    other_user_orchard # Orchard owned by a different user
):
    """
    Tests /api/v1/estimator/estimate for an authenticated user trying to access an orchard they don't own.
    Should return 403 Forbidden.
    """
    mock_run_inference.return_value = MOCK_INFERENCE_RESULTS
    mock_draw_detections.return_value = b"processed_image_bytes"

    response = client.post(
        "/api/v1/estimator/estimate",
        headers=auth_headers,
        params={
            "orchard_id": other_user_orchard.id,
            "preview": False
        },
        files={"file": DUMMY_IMAGE}
    )
    assert response.status_code == 403
    assert "detail" in response.json()
    assert "You can only upload images to orchards that you own" in response.json()["detail"]


@patch("app.api.v1.endpoints.estimator.draw_cyberpunk_detections")
@patch.object(AppleInference, "run_inference")
def test_estimator_guest_with_orchard_or_tree_id_fails(
    mock_run_inference: MagicMock,
    mock_draw_detections: MagicMock,
    client: TestClient,
    test_orchard,
    test_tree
):
    """
    Tests that a guest user attempting to provide orchard_id or tree_id
    to /api/v1/estimator/estimate receives a 400 Bad Request.
    """
    mock_run_inference.return_value = MOCK_INFERENCE_RESULTS
    mock_draw_detections.return_value = b"processed_image_bytes"

    # Try with orchard_id
    response = client.post(
        "/api/v1/estimator/estimate",
        params={
            "orchard_id": test_orchard.id,
            "preview": True
        },
        files={"file": DUMMY_IMAGE}
    )
    assert response.status_code == 400
    assert "detail" in response.json()
    assert "Guest users cannot specify orchard_id or tree_id. Please login first." in response.json()["detail"]

    # Try with tree_id
    response = client.post(
        "/api/v1/estimator/estimate",
        params={
            "tree_id": test_tree.id,
            "preview": True
        },
        files={"file": DUMMY_IMAGE}
    )
    assert response.status_code == 400
    assert "detail" in response.json()
    assert "Guest users cannot specify orchard_id or tree_id. Please login first." in response.json()["detail"]

    # Try with both
    response = client.post(
        "/api/v1/estimator/estimate",
        params={
            "orchard_id": test_orchard.id,
            "tree_id": test_tree.id,
            "preview": True
        },
        files={"file": DUMMY_IMAGE}
    )
    assert response.status_code == 400
    assert "detail" in response.json()
    assert "Guest users cannot specify orchard_id or tree_id. Please login first." in response.json()["detail"]


@patch("app.api.v1.endpoints.estimator.draw_cyberpunk_detections")
@patch.object(AppleInference, "run_inference")
def test_estimator_invalid_image_format(
    mock_run_inference: MagicMock,
    mock_draw_detections: MagicMock,
    client: TestClient
):
    """
    Tests /api/v1/estimator/estimate with an invalid image format.
    Should return 400 Bad Request.
    """
    mock_run_inference.return_value = MOCK_INFERENCE_RESULTS
    mock_draw_detections.return_value = b"processed_image_bytes"

    invalid_image = ("document.txt", b"this is not an image", "text/plain")

    response = client.post(
        "/api/v1/estimator/estimate",
        files={"file": invalid_image}
    )
    assert response.status_code == 400
    assert "detail" in response.json()
    assert "Invalid file format. Allowed: image/jpeg, image/png, image/jpg" in response.json()["detail"]


@patch("app.api.v1.endpoints.estimator.draw_cyberpunk_detections")
@patch.object(AppleInference, "run_inference")
def test_estimator_empty_image_file(
    mock_run_inference: MagicMock,
    mock_draw_detections: MagicMock,
    client: TestClient
):
    """
    Tests /api/v1/estimator/estimate with an empty image file.
    Should return 400 Bad Request.
    """
    mock_run_inference.return_value = MOCK_INFERENCE_RESULTS
    mock_draw_detections.return_value = b"processed_image_bytes"

    empty_image = ("empty.jpg", b"", "image/jpeg")

    response = client.post(
        "/api/v1/estimator/estimate",
        files={"file": empty_image}
    )
    assert response.status_code == 400
    assert "detail" in response.json()
    assert "Empty image file" in response.json()["detail"]


@patch("app.api.v1.endpoints.estimator.draw_cyberpunk_detections")
@patch.object(AppleInference, "run_inference")
def test_estimator_confidence_threshold_parameter(
    mock_run_inference: MagicMock,
    mock_draw_detections: MagicMock,
    client: TestClient,
    auth_headers: dict,
    test_orchard,
    test_tree
):
    """
    Tests /api/v1/estimator/estimate with a specific confidence_threshold.
    Ensures the threshold is passed correctly to inference and drawing functions.
    """
    mock_run_inference.return_value = MOCK_INFERENCE_RESULTS
    mock_draw_detections.return_value = b"processed_image_bytes"

    test_threshold = 0.75

    response = client.post(
        "/api/v1/estimator/estimate",
        headers=auth_headers,
        params={
            "orchard_id": test_orchard.id,
            "tree_id": test_tree.id,
            "preview": True,
            "confidence_threshold": test_threshold
        },
        files={"file": DUMMY_IMAGE}
    )

    assert response.status_code == 200

    # Verify run_inference was called with the correct deep confidence threshold
    mock_run_inference.assert_called_once()
    assert mock_run_inference.call_args[0][1] == 0.64 * test_threshold

    # Verify draw_cyberpunk_detections was called with the correct drawing threshold
    mock_draw_detections.assert_called_once()
    assert mock_draw_detections.call_args[0][2] == 0.85 * test_threshold


# --- Tests for /api/v1/estimator/history ---

def test_get_estimation_history_authenticated_user(client: TestClient, db_session: Session, auth_headers: dict, test_user: User):
    """
    Tests fetching estimation history for an authenticated user with existing records.
    """
    # Create some dummy records for the test user
    record1 = YieldRecord(user_id=test_user.id, filename="file1.jpg", healthy_count=10, damaged_count=2, total_count=12, health_index=83.33)
    record2 = YieldRecord(user_id=test_user.id, filename="file2.jpg", healthy_count=5, damaged_count=1, total_count=6, health_index=83.33)
    # Record for another user (should not be returned)
    record_other = YieldRecord(user_id=test_user.id + 1, filename="file_other.jpg", healthy_count=1, damaged_count=0, total_count=1, health_index=100.00)
    db_session.add_all([record1, record2, record_other])
    db_session.commit()
    db_session.refresh(record1)
    db_session.refresh(record2)
    db_session.refresh(record_other)

    response = client.get(
        "/api/v1/estimator/history",
        headers=auth_headers
    )

    assert response.status_code == 200
    history = response.json()
    assert len(history) == 2
    assert history[0]["healthy_count"] == record2.healthy_count # Should be ordered by created_at desc
    assert history[1]["healthy_count"] == record1.healthy_count


def test_get_estimation_history_no_records(client: TestClient, db_session: Session, auth_headers: dict, test_user: User):
    """
    Tests fetching estimation history for an authenticated user with no records.
    Should return an empty list.
    """
    # Ensure no records exist for the test_user
    assert db_session.query(YieldRecord).filter(YieldRecord.user_id == test_user.id).count() == 0

    response = client.get(
        "/api/v1/estimator/history",
        headers=auth_headers
    )

    assert response.status_code == 200
    history = response.json()
    assert len(history) == 0


def test_get_estimation_history_unauthenticated(client: TestClient):
    """
    Tests fetching estimation history without authentication.
    Should return 401 Unauthorized.
    """
    response = client.get("/api/v1/estimator/history")
    assert response.status_code == 401
    assert "detail" in response.json()
    assert response.json()["detail"] == "Not authenticated"
