import httpx
import json
from typing import Dict, Any
from datetime import datetime
async def send_webhook(url: str, payload: Dict[str, Any]) -> bool:
    """Send a webhook notification."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=10.0
            )
            return response.status_code == 200
    except Exception as e:
        print(f"Webhook error: {e}")
        return False
def create_webhook_payload(document_id: int, status: str, event_type: str) -> Dict:
    """Create webhook payload."""
    return {
        "event": event_type,
        "document_id": document_id,
        "status": status,
        "timestamp": datetime.utcnow().isoformat(),
        "message": f"Document {document_id} status changed to {status}"
    }
