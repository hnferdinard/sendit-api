import pytest
from tests.conftest import client, test_user, admin_headers
def test_register_webhook(client, admin_headers):
    """Test registering a webhook."""
    webhook_data = {
        "url": "https://webhook.site/test",
        "event_type": "document.enriched"
    }
    response = client.post(
        "/webhooks/register",
        json=webhook_data,
        headers=admin_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Webhook registered successfully"
    assert "webhook_id" in data
def test_list_webhooks(client, admin_headers):
    """Test listing webhooks."""
    # Register a webhook first
    webhook_data = {
        "url": "https://webhook.site/test-list",
        "event_type": "document.enriched"
    }
    client.post("/webhooks/register", json=webhook_data, headers=admin_headers)
    # List webhooks
    response = client.get("/webhooks", headers=admin_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
def test_delete_webhook(client, admin_headers):
    """Test deleting a webhook."""
    # Register a webhook
    webhook_data = {
        "url": "https://webhook.site/test-delete",
        "event_type": "document.enriched"
    }
    register_response = client.post(
        "/webhooks/register",
        json=webhook_data,
        headers=admin_headers
    )
    webhook_id = register_response.json()["webhook_id"]
    # Delete the webhook
    response = client.delete(f"/webhooks/{webhook_id}", headers=admin_headers)
    assert response.status_code == 200
