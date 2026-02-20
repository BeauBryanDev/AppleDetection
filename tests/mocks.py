"""
Mock classes for external services to enable fast, isolated testing.
"""
import pytest
from unittest.mock import MagicMock, patch
from typing import Dict, Any, Optional
import os
from pathlib import Path


class MockONNXInference:
    """
    Mock for the AppleInference class that doesn't load real ONNX models.
    """
    
    def __init__(self, model_path: str = None):
        """Initialize with no real model loading."""
        self.session = MagicMock()
        self.input_name = "images"
        self.input_shape = [1, 3, 640, 640]
        self.classes = ["apple", "damaged_apple"]
        
    def _preprocess(self, img_bgr):
        """Mock preprocessing."""
        return MagicMock()
    
    def _classify_apple_color(self, roi):
        """Mock color classification."""
        return 0  # Default to red
    
    def run_inference(self, image_bytes: bytes, confidence_threshold: float = 0.45) -> Dict[str, Any]:
        """
        Mock inference that returns controlled results.
        To be patched in tests with specific return values.
        """
        # This will be overridden by patch in tests
        raise NotImplementedError("Use patch to set return value in tests")


class MockS3Client:
    """
    Mock for boto3 S3 client to avoid real AWS calls.
    """
    
    def __init__(self):
        self.storage = {}  # In-memory storage
        self.calls = []  # Track calls for assertions
    
    def put_object(self, Bucket: str, Key: str, Body: bytes, ContentType: str = None):
        """Mock S3 upload."""
        self.calls.append(("put_object", Bucket, Key))
        self.storage[f"{Bucket}/{Key}"] = Body
        return {"ETag": "mocked-etag"}
    
    def get_object(self, Bucket: str, Key: str):
        """Mock S3 download."""
        self.calls.append(("get_object", Bucket, Key))
        content = self.storage.get(f"{Bucket}/{Key}")
        if content is None:
            raise Exception("NoSuchKey")
        return {"Body": MagicMock(read=MagicMock(return_value=content))}
    
    def delete_object(self, Bucket: str, Key: str):
        """Mock S3 delete."""
        self.calls.append(("delete_object", Bucket, Key))
        self.storage.pop(f"{Bucket}/{Key}", None)
        return {}
    
    def generate_presigned_url(self, ClientMethod: str, Params: dict, ExpiresIn: int):
        """Mock pre-signed URL generation."""
        self.calls.append(("generate_presigned_url", ClientMethod, Params))
        return f"https://mocked-presigned-url.com/{Params['Key']}?expires={ExpiresIn}"


@pytest.fixture
def mock_s3_client():
    """Fixture that provides a mock S3 client."""
    return MockS3Client()


@pytest.fixture
def mock_boto3(monkeypatch, mock_s3_client):
    """Fixture that patches boto3.client to return our mock."""
    
    def mock_boto3_client(service_name, **kwargs):
        if service_name == "s3":
            return mock_s3_client
        return MagicMock()
    
    monkeypatch.setattr("boto3.client", mock_boto3_client)
    return mock_s3_client


class MockFileSystem:
    """
    Mock for file system operations to avoid real disk I/O.
    """
    
    def __init__(self):
        self.files = {}  # In-memory virtual filesystem
        self.dirs = set()
        self.calls = []
    
    def exists(self, path: str) -> bool:
        """Check if file exists."""
        self.calls.append(("exists", path))
        return path in self.files or path in self.dirs
    
    def makedirs(self, path: str, exist_ok: bool = False):
        """Create directory."""
        self.calls.append(("makedirs", path))
        self.dirs.add(path)
    
    def write_bytes(self, path: str, content: bytes):
        """Write bytes to virtual file."""
        self.calls.append(("write_bytes", path))
        parent = str(Path(path).parent)
        if parent:
            self.dirs.add(parent)
        self.files[path] = content
    
    def read_bytes(self, path: str) -> bytes:
        """Read bytes from virtual file."""
        self.calls.append(("read_bytes", path))
        return self.files.get(path, b"")
    
    def remove(self, path: str):
        """Remove file."""
        self.calls.append(("remove", path))
        self.files.pop(path, None)


@pytest.fixture
def mock_fs(monkeypatch):
    """Fixture that patches file system operations."""
    fs = MockFileSystem()
    
    # Patch os.path.exists
    def mock_exists(path):
        return fs.exists(str(path))
    monkeypatch.setattr("os.path.exists", mock_exists)
    
    # Patch os.makedirs
    def mock_makedirs(path, exist_ok=False):
        fs.makedirs(str(path), exist_ok)
    monkeypatch.setattr("os.makedirs", mock_makedirs)
    
    # Patch open for writing
    original_open = open
    
    def mock_open_write(file, mode='r', *args, **kwargs):
        if 'w' in mode or 'b' in mode:
            # For write operations, store in memory
            class MockFile:
                def __init__(self, path, mode):
                    self.path = path
                    self.mode = mode
                    self.content = b''
                
                def __enter__(self):
                    return self
                
                def __exit__(self, *args):
                    if 'b' in self.mode:
                        fs.write_bytes(self.path, self.content)
                
                def write(self, data):
                    if isinstance(data, str):
                        data = data.encode()
                    self.content += data
                
                def close(self):
                    pass
            
            return MockFile(str(file), mode)
        else:
            # For read operations, return from virtual fs
            class MockFile:
                def __init__(self, path, mode):
                    self.path = path
                    self.mode = mode
                    self.content = fs.read_bytes(str(path))
                    self.pos = 0
                
                def __enter__(self):
                    return self
                
                def __exit__(self, *args):
                    pass
                
                def read(self, size=None):
                    if size is None:
                        data = self.content[self.pos:]
                        self.pos = len(self.content)
                        return data
                    else:
                        data = self.content[self.pos:self.pos + size]
                        self.pos += size
                        return data
                
                def close(self):
                    pass
            
            if fs.exists(str(file)):
                return MockFile(str(file), mode)
            else:
                return original_open(file, mode, *args, **kwargs)
    
    monkeypatch.setattr("builtins.open", mock_open_write)
    
    # Patch os.remove
    def mock_remove(path):
        fs.remove(str(path))
    monkeypatch.setattr("os.remove", mock_remove)
    
    return fs


class MockJWT:
    """Helper for JWT token creation in tests."""
    
    @staticmethod
    def create_token(user_id: int, role: str, secret: str = "test-secret", minutes: int = 30):
        """Create a JWT token for testing."""
        import jwt
        from datetime import datetime, timedelta, timezone
        
        expire = datetime.now(timezone.utc) + timedelta(minutes=minutes)
        to_encode = {
            "sub": str(user_id),
            "role": role,
            "exp": expire
        }
        return jwt.encode(to_encode, secret, algorithm="HS256")