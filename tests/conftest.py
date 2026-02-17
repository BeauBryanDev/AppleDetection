import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.db.session import get_db
from app.db.base import Base
from app.core.security import get_password_hash
from app.db.models.users import User, UserRole
from app.db.models.farming import Orchard, Tree, YieldRecord, Image, Prediction, Detection

# ── Test DB (SQLite en memoria) ───────/───────────
TEST_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="module")
def client():
    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

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


@pytest.fixture(scope="function")
def auth_headers(test_user):
    from tests.test_estimator import create_jwt_token # Import the helper
    token = create_jwt_token(test_user.id, test_user.role)
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture(scope="function")
def admin_auth_headers(admin_user):
    from tests.test_estimator import create_jwt_token # Import the helper
    token = create_jwt_token(admin_user.id, admin_user.role)
    return {"Authorization": f"Bearer {token}"}