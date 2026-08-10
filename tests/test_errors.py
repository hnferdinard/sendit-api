import pytest
from tests.conftest import client, test_user, auth_headers
def test_404_error(client):
    """Test 404 error handling."""
    response = client.get("/non-existent-endpoint")
    assert response.status_code == 404
def test_validation_error_upload(client, auth_headers):
    """Test validation error handling for upload."""
    # Try to upload a file with invalid type
    test_file_content = b"Invalid content"
    files = {"file": ("test.exe", test_file_content, "application/exe")}
    data = {"city": "Nairobi", "country": "Kenya"}
    response = client.post(
        "/documents/upload",
        files=files,
        data=data,
        headers=auth_headers
    )
    assert response.status_code == 400
def test_unauthorized_access(client):
    """Test unauthorized access to protected endpoints."""
    response = client.get("/documents")
    assert response.status_code == 401  # Unauthorized
def test_health_endpoint(client):
    """Test health endpoint is accessible without auth."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "SendIt API"
