import pytest
from tests.conftest import client, test_user
def test_register_user(client, test_user):
    """Test user registration."""
    test_user["password"] = "test123"
    response = client.post("/register", json=test_user)
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == test_user["username"]
    assert data["email"] == test_user["email"]
    assert "password" not in data
def test_register_duplicate_user(client, test_user):
    """Test registering with an existing username."""
    test_user["password"] = "test123"
    # First registration
    client.post("/register", json=test_user)
    # Second registration with same username
    duplicate_user = test_user.copy()
    duplicate_user["email"] = "different@example.com"
    response = client.post("/register", json=duplicate_user)
    assert response.status_code == 400
def test_login_user(client, test_user):
    """Test user login."""
    test_user["password"] = "test123"
    # Register first
    client.post("/register", json=test_user)
    # Login
    response = client.post(
        "/login",
        data={"username": test_user["username"], "password": test_user["password"]}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
def test_login_invalid_credentials(client, test_user):
    """Test login with invalid credentials."""
    test_user["password"] = "test123"
    # Register first
    client.post("/register", json=test_user)
    # Login with wrong password
    response = client.post(
        "/login",
        data={"username": test_user["username"], "password": "wrongpass"}
    )
    assert response.status_code == 401
