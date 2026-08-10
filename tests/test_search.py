import pytest
from tests.conftest import client, test_user, auth_headers
def test_search_documents_by_city(client, auth_headers):
    """Test searching documents by city."""
    # Upload a document
    test_file_content = b"Test document for search"
    files = {"file": ("search_test.pdf", test_file_content, "application/pdf")}
    data = {"city": "Nairobi", "country": "Kenya", "description": "Search test"}
    client.post("/documents/upload", files=files, data=data, headers=auth_headers)
    # Search by city
    response = client.get("/documents/search?city=Nairobi", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
def test_search_documents_by_status(client, auth_headers):
    """Test searching documents by status."""
    # Upload a document
    test_file_content = b"Test document for status search"
    files = {"file": ("status_test.pdf", test_file_content, "application/pdf")}
    data = {"city": "Nairobi", "country": "Kenya"}
    client.post("/documents/upload", files=files, data=data, headers=auth_headers)
    # Search by status
    response = client.get("/documents/search?status=enriched", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 0
def test_search_documents_by_keyword(client, auth_headers):
    """Test searching documents by keyword."""
    # Upload a document
    test_file_content = b"Test document for keyword search"
    files = {"file": ("keyword_test.pdf", test_file_content, "application/pdf")}
    data = {"city": "Nairobi", "country": "Kenya", "description": "UniqueKeyword123"}
    client.post("/documents/upload", files=files, data=data, headers=auth_headers)
    # Search by keyword
    response = client.get("/documents/search?q=UniqueKeyword123", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
