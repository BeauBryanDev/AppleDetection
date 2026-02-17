import pytest
import os
import shutil
import uuid
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from app.main import app
from app.models.inference import AppleInference

client = TestClient(app)

def test_path_traversal_behavior():
    """
    Test if f'{uuid}_{filename}' allows path traversal.
    """
    # 1. Simulate the potentially vulnerable filename
    # If attacker sends "../test_traversal.txt"
    # And code does: unique_filename = f"{uuid.uuid4()}_{file.filename}"
    
    # Let's verify what happens with open() directly first.
    
    test_uuid = "test-uuid"
    malicious_filename = "../traversal_test_file.txt"
    
    combined_name = f"{test_uuid}_{malicious_filename}"
    path = f"uploads/{combined_name}"
    
    # Path is "uploads/test-uuid_../traversal_test_file.txt"
    # This should be treated as a file named "test-uuid_../traversal_test_file.txt" INSIDE uploads/
    # UNLESS ".." is interpreted.
    
    # Let's verify this behavior on the actual filesystem
    os.makedirs("uploads", exist_ok=True)
    
    try:
        with open(path, "wb") as f:
            f.write(b"test")
            
        print(f"Created file at: {path}")
        print(f"Abspath: {os.path.abspath(path)}")
        
        # Check if it traversed
        # If it traversed to root, then "traversal_test_file.txt" should exist 
        # But wait, "uploads/test-uuid_../" -> "uploads/.." ?? No.
        
        # The only way this traverses is if "test-uuid_" is a directory that exists and contains ".." ??
        # Or if "test-uuid_.." is somehow special.
        
    except Exception as e:
        print(f"Failed to open/write: {e}")

    # Now let's try via the API to be sure
    
    with patch.object(AppleInference, "run_inference") as mock_inference:
        mock_inference.return_value = {
            "counts": {"healthy": 0, "damaged_apple": 0, "total": 0, "red_apple": 0, "green_apple": 0},
            "detections": {"boxes": [], "class_ids": [], "confidences": []}
        }
        
        files = {"file": (malicious_filename, b"content", "image/jpeg")}
        
        # We expect this to either fail (500) or save safely.
        # If it saves safely, the vulnerability might be misunderstood or the UUID prefix mitigates it.
        # BUT we should fix it anyway because clean filenames are better.
        
        response = client.post(
            "/api/v1/estimator/estimate", 
            files=files,
            data={"preview": "false", "orchard_id": "1"} # Guest mode or auth?
        )
        # Guest mode works without orchard_id.
        if response.status_code != 200:
             # Try guest mode
             response = client.post(
                "/api/v1/estimator/estimate", 
                files=files,
                data={"preview": "false"}
            )
             
        print(f"Response: {response.status_code}")
        print(f"Headers: {response.headers}")
        
        if "X-Image-Path" in response.headers:
            saved_path = response.headers["X-Image-Path"]
            print(f"Saved Path Header: {saved_path}")
            if "../" in saved_path:
                print("Traversal sequence found in path!")

if __name__ == "__main__":
    test_path_traversal_behavior()
