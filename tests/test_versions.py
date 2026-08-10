import pytest
from tests.conftest import client, test_user, auth_headers
def test_document_versioning(client, auth_headers):
    """Test document versioning."""
    # Upload first version
    test_file_content = b"Version 1 content"
    files = {"file": ("version_test.pdf", test_file_content, "application/pdf")}
    data = {"city": "Nairobi", "country": "Kenya", "description": "Version 1"}
    response1 = client.post("/documents/upload", files=files, data=data, headers=auth_headers)
    doc_id1 = response1.json()["document_id"]
    # Upload second version (same filename)
    test_file_content2 = b"Version 2 content - Updated"
    files2 = {"file": ("version_test.pdf", test_file_content2, "application/pdf")}
    response2 = client.post("/documents/upload", files=files2, data=data, headers=auth_headers)
    doc_id2 = response2.json()["document_id"]
    # Check that version numbers increased
    assert response2.json()["version"] > response1.json()["version"]
    # Get version history
    response = client.get(f"/documents/{doc_id2}/versions", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total_versions"] >= 2
