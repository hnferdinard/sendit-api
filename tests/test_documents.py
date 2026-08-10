import pytest
import os
from tests.conftest import client, test_user, auth_headers
def test_upload_document(client, auth_headers):
    """Test uploading a document."""
    # Create a test file
    test_file_content = b"Test document content for upload"
    files = {"file": ("test.pdf", test_file_content, "application/pdf")}
    data = {
        "city": "Nairobi",
        "country": "Kenya",
        "description": "Test document"
    }
    response = client.post(
        "/documents/upload",
        files=files,
        data=data,
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Document uploaded successfully"
    assert "document_id" in data
    assert data["status"] in ["uploaded", "enriched"]
def test_list_documents(client, auth_headers):
    """Test listing documents."""
    # Upload a document first
    test_file_content = b"Test document for listing"
    files = {"file": ("list_test.pdf", test_file_content, "application/pdf")}
    data = {"city": "Nairobi", "country": "Kenya"}
    client.post("/documents/upload", files=files, data=data, headers=auth_headers)
    # List documents
    response = client.get("/documents", headers=auth_headers)
    assert response.status_code == 200
    documents = response.json()
    assert len(documents) >= 1
def test_get_document(client, auth_headers):
    """Test getting a single document."""
    # Upload a document
    test_file_content = b"Test document for getting"
    files = {"file": ("get_test.pdf", test_file_content, "application/pdf")}
    data = {"city": "Nairobi", "country": "Kenya"}
    upload_response = client.post(
        "/documents/upload",
        files=files,
        data=data,
        headers=auth_headers
    )
    document_id = upload_response.json()["document_id"]
    # Get the document
    response = client.get(f"/documents/{document_id}", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["id"] == document_id
def test_get_document_not_found(client, auth_headers):
    """Test getting a non-existent document."""
    response = client.get("/documents/99999", headers=auth_headers)
    assert response.status_code == 404
def test_delete_document_admin(client, admin_headers):
    """Test deleting a document (admin only)."""
    # Upload a document first
    test_file_content = b"Test document for deletion"
    files = {"file": ("delete_test.pdf", test_file_content, "application/pdf")}
    data = {"city": "Nairobi", "country": "Kenya"}
    upload_response = client.post(
        "/documents/upload",
        files=files,
        data=data,
        headers=admin_headers
    )
    document_id = upload_response.json()["document_id"]
    # Delete the document
    response = client.delete(f"/documents/{document_id}", headers=admin_headers)
    assert response.status_code == 200
    # Verify deletion
    response = client.get(f"/documents/{document_id}", headers=admin_headers)
    assert response.status_code == 404
