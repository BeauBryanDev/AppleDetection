import pytest
import os
import sys
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Set test environment variables BEFORE importing app modules
os.environ["TESTING"] = "true"
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["SECRET_KEY"] = "test-secret-key-for-testing-only-32chars-long"

# Now import app modules
from app.main import app
from app.db.session import get_db
from app.db.base import Base
from app.core.security import get_password_hash
from app.db.models.users import User, UserRole
from app.db.models.farming import Orchard, Tree, YieldRecord, Image, Prediction, Detection

# ── Test DB (SQLite en memoria) ──────────────────────────────────────────────
TEST_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,  # Use static pool for in-memory SQLite
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database session for each test."""
    # Create all tables
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        # Drop all tables after test
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    """Create a test client with database override."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass  # db_session is handled by the db_session fixture

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def test_user(db_session):
    user = User(
        name="Test Farmer",
        email="testfarmer@example.com",
        password_hash=get_password_hash("testpass123"),
        phone_number="+573001234567",
        role=UserRole.FARMER
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture(scope="function")
def admin_user(db_session):
    user = User(
        name="Test Admin",
        email="testadmin@example.com",
        password_hash=get_password_hash("adminpass123"),
        phone_number="+573009876543",
        role=UserRole.ADMIN
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture(scope="function")
def other_user(db_session):
    user = User(
        name="Other Farmer",
        email="otherfarmer@example.com",
        password_hash=get_password_hash("otherpass123"),
        phone_number="+573001112233",
        role=UserRole.FARMER
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture(scope="function")
def test_orchard(db_session, test_user):
    orchard = Orchard(
        user_id=test_user.id,
        name="Test Orchard",
        location="Test Location",
        n_trees=10,
        address="123 Test St"
    )
    db_session.add(orchard)
    db_session.commit()
    db_session.refresh(orchard)
    return orchard


@pytest.fixture(scope="function")
def test_tree(db_session, test_orchard, test_user):
    tree = Tree(
        user_id=test_user.id,
        orchard_id=test_orchard.id,
        tree_code="TR001",
        tree_type="Apple"
    )
    db_session.add(tree)
    db_session.commit()
    db_session.refresh(tree)
    return tree


@pytest.fixture(scope="function")
def other_user_orchard(db_session, other_user):
    orchard = Orchard(
        user_id=other_user.id,
        name="Other User Orchard",
        location="Another Location",
        n_trees=5,
        address="456 Other Rd"
    )
    db_session.add(orchard)
    db_session.commit()
    db_session.refresh(orchard)
    return orchard


# JWT Token helper function for tests
def create_jwt_token(user_id: int, role: UserRole, expires_delta=None):
    """Create a JWT token for testing."""
    from datetime import datetime, timedelta, timezone
    from app.core.config import settings
    import jwt
    
    if expires_delta is None:
        expires_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    expire = datetime.now(timezone.utc) + expires_delta
    to_encode = {"sub": str(user_id), "role": role.value, "exp": expire}
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


@pytest.fixture(scope="function")
def auth_headers(test_user):
    token = create_jwt_token(test_user.id, test_user.role)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="function")
def admin_auth_headers(admin_user):
    token = create_jwt_token(admin_user.id, admin_user.role)
    return {"Authorization": f"Bearer {token}"}