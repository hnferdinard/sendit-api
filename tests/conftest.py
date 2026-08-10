import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from main import app, get_session
import os
# Use in-memory SQLite
TEST_DATABASE_URL = "sqlite:///:memory:"
@pytest.fixture(scope="function")
def client():
    """Create a test client with clean database."""
    engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(engine)
    def get_test_session():
        with Session(engine) as session:
            yield session
    app.dependency_overrides[get_session] = get_test_session
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
@pytest.fixture
def test_user():
    return {
        "username": "testuser",
        "email": "test@example.com",
        "password": "test123",
        "full_name": "Test User",
        "role": "staff"
    }
@pytest.fixture
def test_admin():
    return {
        "username": "adminuser",
        "email": "admin@example.com",
        "password": "admin123",
        "full_name": "Admin User",
        "role": "admin"
    }
@pytest.fixture
def auth_headers(client, test_user):
    client.post("/register", json=test_user)
    response = client.post(
        "/login",
        data={"username": test_user["username"], "password": test_user["password"]}
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
@pytest.fixture
def admin_headers(client, test_admin):
    client.post("/register", json=test_admin)
    response = client.post(
        "/login",
        data={"username": test_admin["username"], "password": test_admin["password"]}
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
