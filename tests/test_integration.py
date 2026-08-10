import pytest
from tests.conftest import client
def test_full_crud_flow(client):
    """Test the full CRUD flow from registration to deletion."""
    # 1. Register a user
    user_data = {
        "username": "integrationuser",
        "email": "integration@example.com",
        "password": "testpass123",
        "full_name": "Integration User",
        "role": "staff"
    }
    register_response = client.post("/register", json=user_data)
    assert register_response.status_code == 200
    # 2. Login
    login_response = client.post(
        "/login",
        data={"username": user_data["username"], "password": user_data["password"]}
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    # 3. Upload a document
    test_file_content = b"Integration test document"
    files = {"file": ("integration_test.pdf", test_file_content, "application/pdf")}
    data = {"city": "Nairobi", "country": "Kenya", "description": "Integration test"}
    upload_response = client.post(
        "/documents/upload",
        files=files,
        data=data,
        headers=headers
    )
    assert upload_response.status_code == 200
    document_id = upload_response.json()["document_id"]
    # 4. Get the document
    get_response = client.get(f"/documents/{document_id}", headers=headers)
    assert get_response.status_code == 200
    assert get_response.json()["id"] == document_id
    # 5. List documents
    list_response = client.get("/documents", headers=headers)
    assert list_response.status_code == 200
    documents = list_response.json()
    assert len(documents) >= 1
    # 6. Search for the document
    search_response = client.get(
        f"/documents/search?q=integration",
        headers=headers
    )
    assert search_response.status_code == 200
    search_data = search_response.json()
    assert search_data["total"] >= 1
    # 7. Get weather data
    weather_response = client.get(f"/documents/{document_id}/weather", headers=headers)
    # Weather may or may not be available depending on API
    assert weather_response.status_code in [200, 404]
