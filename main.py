from fastapi import FastAPI, File, UploadFile, HTTPException, Depends, Request, Form
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import os
import uvicorn
import json
import aiofiles
import shutil
app = FastAPI(
    title="SendIt API",
    version="1.0.0",
    description="📄 Document Management & Enrichment Service"
)
# ============ MOUNT STATIC FILES ============
# This serves your background image from the static folder
app.mount("/static", StaticFiles(directory="static"), name="static")
# ============ CREATE UPLOAD DIRECTORY ============
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)
# ============ MODELS ============
class UserRegister(BaseModel):
    username: str
    email: str
    password: str
    full_name: str
    role: str = "staff"
class UserLogin(BaseModel):
    username: str
    password: str
class DocumentCreate(BaseModel):
    city: str
    country: str = "Kenya"
    description: Optional[str] = None
class DocumentUpdate(BaseModel):
    city: Optional[str] = None
    country: Optional[str] = None
    description: Optional[str] = None
class WebhookCreate(BaseModel):
    url: str
    event_type: str
# ============ IN-MEMORY STORAGE ============
users_db = {}
tokens_db = {}
documents_db = {}
webhooks_db = {}
document_counter = 0
# ============ AUTHENTICATION ============
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login", auto_error=False)
async def get_current_user(token: str = Depends(oauth2_scheme)):
    if not token:
        raise HTTPException(401, "Not authenticated")
    if token not in tokens_db:
        raise HTTPException(401, "Invalid token")
    username = tokens_db[token]
    if username not in users_db:
        raise HTTPException(401, "User not found")
    return users_db[username]
async def get_current_admin(current_user: dict = Depends(get_current_user)):
    if current_user.get("role") != "admin":
        raise HTTPException(403, "Admin access required")
    return current_user
async def get_current_manager(current_user: dict = Depends(get_current_user)):
    if current_user.get("role") not in ["admin", "manager"]:
        raise HTTPException(403, "Manager or admin access required")
    return current_user
# ============ WEATHER SERVICE ============
async def get_weather(city: str, country: str = "Kenya"):
    return {
        "city": city,
        "country": country,
        "temperature": 25.5,
        "windspeed": 10.2,
        "weathercode": 1,
        "time": datetime.now().isoformat(),
        "source": "Mock Weather API"
    }
# ============ WEBHOOK SERVICE ============
async def send_webhook(url: str, payload: dict):
    print(f"🔔 Webhook sent to {url}: {payload}")
    return True
def create_webhook_payload(document_id: int, status: str, event_type: str):
    return {
        "event": event_type,
        "document_id": document_id,
        "status": status,
        "timestamp": datetime.now().isoformat(),
        "message": f"Document {document_id} status changed to {status}"
    }
# ============ CUSTOM CSS WITH BACKGROUND ============
custom_css = f"""
<style>
    /* Full page background using your image */
    body {{
        background-image: url('/static/background.jpg');
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
        background-repeat: no-repeat;
        min-height: 100vh;
    }}
    /* Make Swagger UI semi-transparent */
    .swagger-ui {{
        background: rgba(255, 255, 255, 0.92);
        border-radius: 15px;
        padding: 20px;
        margin: 20px;
        backdrop-filter: blur(10px);
        box-shadow: 0 8px 32px rgba(0,0,0,0.3);
    }}
    /* Top bar styling */
    .swagger-ui .topbar {{
        background: rgba(0, 0, 0, 0.7) !important;
        border-radius: 10px 10px 0 0;
        padding: 15px !important;
    }}
    .swagger-ui .topbar .download-url-wrapper .select-label {{
        color: #fff !important;
    }}
    /* Info section */
    .swagger-ui .info .title {{
        color: #1a1a2e !important;
        text-shadow: 2px 2px 4px rgba(255,255,255,0.5);
    }}
    /* Buttons */
    .swagger-ui .btn {{
        border-radius: 8px !important;
        font-weight: bold !important;
    }}
    .swagger-ui .btn.execute {{
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        color: white !important;
        border: none !important;
    }}
    .swagger-ui .btn.execute:hover {{
        transform: scale(1.05);
        transition: all 0.3s ease;
    }}
    .swagger-ui .btn.try-out__btn {{
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%) !important;
        color: white !important;
        border: none !important;
    }}
    .swagger-ui .btn.try-out__btn:hover {{
        transform: scale(1.05);
        transition: all 0.3s ease;
    }}
    /* Response section */
    .swagger-ui .responses-wrapper {{
        background: rgba(255, 255, 255, 0.9);
        border-radius: 10px;
        padding: 10px;
    }}
    /* Model boxes */
    .swagger-ui .model-box {{
        background: rgba(255, 255, 255, 0.9);
        border-radius: 8px;
    }}
</style>
"""
# Inject custom CSS into Swagger UI
app.openapi_url = "/openapi.json"
@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    html = app.swagger_ui_html(
        openapi_url="/openapi.json",
        title="SendIt API - Document Management",
        swagger_js_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js",
        swagger_css_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css",
        swagger_favicon_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/favicon-32x32.png"
    )
    html.body = html.body.replace(
        '</head>',
        f'{custom_css}</head>'
    )
    return html
# ============ HEALTH ENDPOINTS ============
@app.get("/")
@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "SendIt API",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat(),
        "uptime": "🚀 Live on Render!"
    }
# ============ AUTHENTICATION ENDPOINTS ============
@app.post("/register")
async def register(user: UserRegister):
    if user.username in users_db:
        raise HTTPException(400, "Username already registered")
    users_db[user.username] = user.dict()
    return {
        "message": "User registered successfully",
        "user_id": len(users_db),
        "username": user.username,
        "email": user.email,
        "role": user.role
    }
@app.post("/login")
async def login(
    username: Optional[str] = Form(None),
    password: Optional[str] = Form(None),
    user_data: Optional[UserLogin] = None
):
    if user_data:
        username = user_data.username
        password = user_data.password
    if not username or not password:
        raise HTTPException(400, "Username and password required")
    if username not in users_db:
        raise HTTPException(401, "Invalid credentials")
    if users_db[username]["password"] != password:
        raise HTTPException(401, "Invalid credentials")
    token = f"token-{username}-{os.urandom(8).hex()}"
    tokens_db[token] = username
    return {"access_token": token, "token_type": "bearer"}
# ============ DOCUMENT ENDPOINTS ============
@app.post("/documents/upload")
async def upload_document(
    file: UploadFile = File(...),
    city: str = Form(...),
    description: Optional[str] = Form(None),
    country: str = Form("Kenya"),
    current_user: dict = Depends(get_current_user)
):
    global document_counter
    allowed_extensions = [".pdf", ".jpg", ".jpeg", ".png", ".docx", ".txt"]
    file_extension = os.path.splitext(file.filename)[1].lower()
    if file_extension not in allowed_extensions:
        raise HTTPException(400, f"File type not allowed. Allowed: {', '.join(allowed_extensions)}")
    contents = await file.read()
    file_size = len(contents)
    max_size = 5 * 1024 * 1024
    if file_size > max_size:
        raise HTTPException(400, f"File too large. Max size: {max_size // (1024 * 1024)} MB")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_filename = f"{timestamp}_{file.filename.replace(' ', '_')}"
    file_path = os.path.join(UPLOAD_DIR, safe_filename)
    async with aiofiles.open(file_path, 'wb') as out_file:
        await out_file.write(contents)
    existing_version = None
    for doc in documents_db.values():
        if doc["original_filename"] == file.filename and doc["uploader_id"] == current_user["username"]:
            if not existing_version or doc["version"] > existing_version:
                existing_version = doc["version"]
    version = 1 if not existing_version else existing_version + 1
    document_counter += 1
    document = {
        "id": document_counter,
        "filename": safe_filename,
        "original_filename": file.filename,
        "file_size": file_size,
        "file_type": file.content_type or "application/octet-stream",
        "city": city,
        "country": country,
        "description": description,
        "uploader_id": current_user["username"],
        "file_path": file_path,
        "status": "processing",
        "version": version,
        "uploaded_at": datetime.now().isoformat(),
        "weather_data": None,
        "weather_fetched_at": None
    }
    documents_db[document_counter] = document
    try:
        weather_data = await get_weather(city, country)
        if weather_data:
            document["weather_data"] = json.dumps(weather_data)
            document["weather_fetched_at"] = datetime.now().isoformat()
            document["status"] = "enriched"
            webhooks = [w for w in webhooks_db.values() if w["event_type"] == "document.enriched"]
            for webhook in webhooks:
                payload = create_webhook_payload(document_counter, "enriched", "document.enriched")
                await send_webhook(webhook["url"], payload)
    except Exception as e:
        print(f"Weather API error: {e}")
        document["status"] = "uploaded"
    documents_db[document_counter] = document
    return {
        "message": "Document uploaded successfully",
        "document_id": document_counter,
        "filename": file.filename,
        "status": document["status"],
        "version": document["version"]
    }
@app.get("/documents")
async def list_documents(
    status: Optional[str] = None,
    city: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    docs = list(documents_db.values())
    if current_user.get("role") not in ["admin", "manager"]:
        docs = [d for d in docs if d["uploader_id"] == current_user["username"]]
    if status:
        docs = [d for d in docs if d["status"] == status]
    if city:
        docs = [d for d in docs if d["city"].lower() == city.lower()]
    return docs
@app.get("/documents/{document_id}")
async def get_document(
    document_id: int,
    current_user: dict = Depends(get_current_user)
):
    if document_id not in documents_db:
        raise HTTPException(404, "Document not found")
    document = documents_db[document_id]
    if current_user.get("role") not in ["admin", "manager"] and document["uploader_id"] != current_user["username"]:
        raise HTTPException(403, "Access denied")
    return document
@app.get("/documents/search")
async def search_documents(
    q: Optional[str] = None,
    city: Optional[str] = None,
    status: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    docs = list(documents_db.values())
    if current_user.get("role") not in ["admin", "manager"]:
        docs = [d for d in docs if d["uploader_id"] == current_user["username"]]
    if city:
        docs = [d for d in docs if city.lower() in d["city"].lower()]
    if status:
        docs = [d for d in docs if d["status"] == status]
    if q:
        docs = [d for d in docs if q.lower() in d.get("description", "").lower() or q.lower() in d["original_filename"].lower()]
    return {"total": len(docs), "documents": docs}
@app.get("/documents/{document_id}/versions")
async def get_document_versions(
    document_id: int,
    current_user: dict = Depends(get_current_user)
):
    if document_id not in documents_db:
        raise HTTPException(404, "Document not found")
    original = documents_db[document_id]
    if current_user.get("role") not in ["admin", "manager"] and original["uploader_id"] != current_user["username"]:
        raise HTTPException(403, "Access denied")
    versions = [d for d in documents_db.values() if d["original_filename"] == original["original_filename"]]
    versions.sort(key=lambda x: x["version"], reverse=True)
    return {
        "original_filename": original["original_filename"],
        "total_versions": len(versions),
        "versions": versions
    }
@app.get("/documents/{document_id}/weather")
async def get_document_weather(
    document_id: int,
    current_user: dict = Depends(get_current_user)
):
    if document_id not in documents_db:
        raise HTTPException(404, "Document not found")
    document = documents_db[document_id]
    if current_user.get("role") not in ["admin", "manager"] and document["uploader_id"] != current_user["username"]:
        raise HTTPException(403, "Access denied")
    if not document.get("weather_data"):
        raise HTTPException(404, "No weather data available for this document")
    return {
        "document_id": document_id,
        "city": document["city"],
        "country": document["country"],
        "weather": json.loads(document["weather_data"])
    }
@app.post("/documents/{document_id}/enrich")
async def enrich_document(
    document_id: int,
    current_user: dict = Depends(get_current_manager)
):
    if document_id not in documents_db:
        raise HTTPException(404, "Document not found")
    document = documents_db[document_id]
    if document["status"] == "enriched":
        return {"message": "Document already enriched"}
    try:
        weather_data = await get_weather(document["city"], document["country"])
        if weather_data:
            document["weather_data"] = json.dumps(weather_data)
            document["weather_fetched_at"] = datetime.now().isoformat()
            document["status"] = "enriched"
            documents_db[document_id] = document
            return {"message": "Document enriched successfully", "weather": weather_data}
        else:
            document["status"] = "failed"
            documents_db[document_id] = document
            raise HTTPException(500, "Failed to enrich document with weather data")
    except Exception as e:
        document["status"] = "failed"
        documents_db[document_id] = document
        raise HTTPException(500, f"Failed to enrich document: {str(e)}")
@app.delete("/documents/{document_id}")
async def delete_document(
    document_id: int,
    current_user: dict = Depends(get_current_manager)
):
    if document_id not in documents_db:
        raise HTTPException(404, "Document not found")
    document = documents_db[document_id]
    if os.path.exists(document["file_path"]):
        os.remove(document["file_path"])
    del documents_db[document_id]
    return {"message": "Document deleted successfully"}
# ============ WEBHOOK ENDPOINTS ============
@app.post("/webhooks/register")
async def register_webhook(
    webhook_data: WebhookCreate,
    current_user: dict = Depends(get_current_admin)
):
    webhook_id = len(webhooks_db) + 1
    webhooks_db[webhook_id] = {
        "id": webhook_id,
        "url": webhook_data.url,
        "event_type": webhook_data.event_type,
        "user_id": current_user["username"],
        "created_at": datetime.now().isoformat(),
        "is_active": True
    }
    return {
        "message": "Webhook registered successfully",
        "webhook_id": webhook_id,
        "event_type": webhook_data.event_type
    }
@app.get("/webhooks")
async def list_webhooks(
    current_user: dict = Depends(get_current_admin)
):
    return list(webhooks_db.values())
@app.delete("/webhooks/{webhook_id}")
async def delete_webhook(
    webhook_id: int,
    current_user: dict = Depends(get_current_admin)
):
    if webhook_id not in webhooks_db:
        raise HTTPException(404, "Webhook not found")
    del webhooks_db[webhook_id]
    return {"message": "Webhook deleted successfully"}
# ============ METRICS ENDPOINT ============
@app.get("/metrics")
async def get_metrics(current_user: dict = Depends(get_current_admin)):
    return {
        "total_users": len(users_db),
        "total_documents": len(documents_db),
        "total_webhooks": len(webhooks_db),
        "active_tokens": len(tokens_db),
        "storage_usage": "N/A (in-memory)"
    }
if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
@app.get("/")
async def root():
    return {
        "message": "Welcome to SendIt API! 🚀",
        "docs": "/docs",
        "health": "/health",
        "version": "1.0.0",
        "status": "API is live and running"
    }
