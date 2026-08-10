from fastapi import FastAPI, File, UploadFile, HTTPException, Depends, status, Request, Form
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session, select
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from datetime import datetime
import os
import shutil
import aiofiles
import json
from typing import Optional
from database.session import get_session, create_db_and_tables
from models.user import User, UserCreate, UserResponse
from models.document import Document, DocumentCreate, DocumentUpdate
from auth import (
    hash_password, verify_password, create_access_token,
    get_current_user, get_current_admin, get_current_manager
)
from services.weather import get_weather

from datetime import datetime
from typing import Optional
import aiofiles
import json
import os
import shutil
# Missing imports for webhooks
from models.webhook import Webhook, WebhookCreate
from services.webhook import send_webhook, create_webhook_payload
app = FastAPI(title="SendIt API", version="1.0.0")
# Configuration
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)
MAX_FILE_SIZE = int(os.getenv("MAX_UPLOAD_SIZE", 5 * 1024 * 1024))
ALLOWED_EXTENSIONS = [".pdf", ".jpg", ".jpeg", ".png", ".docx"]
# Rate Limiting
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
@app.on_event("startup")
def on_startup():
    create_db_and_tables()
# Authentication Endpoints
@app.post("/register")
async def register(user_data: UserCreate, session: Session = Depends(get_session)):
    try:
        # Check if username exists
        existing_user = session.exec(select(User).where(User.username == user_data.username)).first()
        if existing_user:
            raise HTTPException(400, "Username already registered")
        # Check if email exists
        existing_email = session.exec(select(User).where(User.email == user_data.email)).first()
        if existing_email:
            raise HTTPException(400, "Email already registered")
        # Hash password and create user
        hashed = hash_password(user_data.password)
        user = User(
            username=user_data.username,
            email=user_data.email,
            hashed_password=hashed,
            full_name=user_data.full_name,
            role=user_data.role
        )
        session.add(user)
        session.commit()
        session.refresh(user)
        return {
            "message": "User registered successfully", 
            "user_id": user.id,
            "username": user.username,
            "role": user.role
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Registration error: {e}")
        raise HTTPException(500, f"Registration failed: {str(e)}")
@app.post("/login")
@limiter.limit("10/minute")
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: Session = Depends(get_session)
):
    user = session.exec(select(User).where(User.username == form_data.username)).first()
    if not user:
        raise HTTPException(401, "Invalid credentials")
    if not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(401, "Invalid credentials")
    if not user.is_active:
        raise HTTPException(403, "User is inactive")
    access_token = create_access_token({"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}
# ... rest of your endpoints ...

# ============ DOCUMENT UPLOAD ENDPOINT ============
@app.post("/documents/upload")
@limiter.limit("10/hour")
async def upload_document(
    request: Request,
    file: UploadFile = File(...),
    city: str = Form(...),
    description: Optional[str] = Form(None),
    country: str = Form("Kenya"),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Upload a document with validation. Enriches with weather data."""
    # Validate file extension
    file_extension = os.path.splitext(file.filename)[1].lower()
    if file_extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(400, f"File type not allowed. Allowed: {', '.join(ALLOWED_EXTENSIONS)}")
    # Read and validate file size
    contents = await file.read()
    file_size = len(contents)
    if file_size > MAX_FILE_SIZE:
        raise HTTPException(400, f"File too large. Max size: {MAX_FILE_SIZE // (1024 * 1024)} MB")
    # Generate safe filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_filename = f"{timestamp}_{current_user.id}_{file.filename.replace(' ', '_')}"
    file_path = os.path.join(UPLOAD_DIR, safe_filename)
    # Save file asynchronously
    async with aiofiles.open(file_path, 'wb') as out_file:
        await out_file.write(contents)
    # Create document record with versioning
    # Check if a document with same name exists for this user
    existing = session.exec(
        select(Document).where(
            Document.original_filename == file.filename,
            Document.uploader_id == current_user.id
        )
    ).first()
    version = 1
    if existing:
        version = existing.version + 1
    document = Document(
        filename=safe_filename,
        original_filename=file.filename,
        file_size=file_size,
        file_type=file.content_type or "application/octet-stream",
        city=city,
        country=country,
        description=description,
        uploader_id=current_user.id,
        file_path=file_path,
        status="processing",
        version=version
    )
    session.add(document)
    session.commit()
    session.refresh(document)
    # Enrich with weather data
    try:
        weather_data = await get_weather(city, country)
        if weather_data:
            document.weather_data = json.dumps(weather_data)
            document.weather_fetched_at = datetime.utcnow()
            document.status = "enriched"
            session.commit()
            # Send webhook notification if document is enriched
            webhooks = session.exec(
                select(Webhook).where(
                    Webhook.event_type == "document.enriched",
                    Webhook.is_active == True
                )
            ).all()
            for webhook in webhooks:
                payload = create_webhook_payload(
                    document.id,
                    document.status,
                    "document.enriched"
                )
                # In production, use background tasks
                await send_webhook(webhook.url, payload)
    except Exception as e:
        print(f"Weather API error: {e}")
        document.status = "uploaded"
        session.commit()
    return {
        "message": "Document uploaded successfully",
        "document_id": document.id,
        "filename": document.original_filename,
        "status": document.status,
        "version": document.version
    }
# ============ LIST DOCUMENTS ENDPOINT ============
@app.get("/documents")
@limiter.limit("30/minute")
def list_documents(
    request: Request,
    status: Optional[str] = None,
    city: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """List all documents with optional filters."""
    query = select(Document)
    if current_user.role not in ["admin", "manager"]:
        query = query.where(Document.uploader_id == current_user.id)
    if status:
        query = query.where(Document.status == status)
    if city:
        query = query.where(Document.city == city)
    return session.exec(query).all()
# ============ GET DOCUMENT ENDPOINT ============
@app.get("/documents/{document_id}")
@limiter.limit("30/minute")
def get_document(
    request: Request,
    document_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Get a specific document."""
    document = session.get(Document, document_id)
    if not document:
        raise HTTPException(404, "Document not found")
    if current_user.role not in ["admin", "manager"] and document.uploader_id != current_user.id:
        raise HTTPException(403, "Access denied")
    return document
# ============ DELETE DOCUMENT ENDPOINT ============
@app.delete("/documents/{document_id}")
def delete_document(
    document_id: int,
    current_user: User = Depends(get_current_manager),
    session: Session = Depends(get_session)
):
    """Delete a document (managers and admins only)."""
    document = session.get(Document, document_id)
    if not document:
        raise HTTPException(404, "Document not found")
    if os.path.exists(document.file_path):
        os.remove(document.file_path)
    session.delete(document)
    session.commit()
    return {"message": "Document deleted successfully"}
# ============ SEARCH ENDPOINT (Exercise 1) ============
@app.get("/documents/search")
@limiter.limit("20/minute")
def search_documents(
    request: Request,
    q: Optional[str] = None,
    city: Optional[str] = None,
    status: Optional[str] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Search documents with multiple filters."""
    query = select(Document)
    # Staff can only see their own documents
    if current_user.role not in ["admin", "manager"]:
        query = query.where(Document.uploader_id == current_user.id)
    # Apply filters
    if city:
        query = query.where(Document.city.ilike(f"%{city}%"))
    if status:
        query = query.where(Document.status == status)
    if date_from:
        query = query.where(Document.uploaded_at >= date_from)
    if date_to:
        query = query.where(Document.uploaded_at <= date_to)
    if q:
        query = query.where(
            (Document.original_filename.ilike(f"%{q}%")) |
            (Document.description.ilike(f"%{q}%"))
        )
    query = query.order_by(Document.uploaded_at.desc())
    results = session.exec(query).all()
    return {
        "total": len(results),
        "documents": results
    }
# ============ VERSIONS ENDPOINT (Exercise 2) ============
@app.get("/documents/{document_id}/versions")
@limiter.limit("30/minute")
def get_document_versions(
    request: Request,
    document_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Get all versions of a document."""
    original = session.get(Document, document_id)
    if not original:
        raise HTTPException(404, "Document not found")
    if current_user.role not in ["admin", "manager"] and original.uploader_id != current_user.id:
        raise HTTPException(403, "Access denied")
    versions = session.exec(
        select(Document).where(
            Document.original_filename == original.original_filename,
            Document.uploader_id == original.uploader_id
        ).order_by(Document.version.desc())
    ).all()
    return {
        "original_filename": original.original_filename,
        "total_versions": len(versions),
        "versions": versions
    }
# ============ ENRICH ENDPOINT ============
@app.post("/documents/{document_id}/enrich")
@limiter.limit("5/minute")
async def enrich_document(
    request: Request,
    document_id: int,
    current_user: User = Depends(get_current_manager),
    session: Session = Depends(get_session)
):
    """Manually trigger weather enrichment for a document."""
    document = session.get(Document, document_id)
    if not document:
        raise HTTPException(404, "Document not found")
    if document.status == "enriched":
        return {"message": "Document already enriched"}
    weather_data = await get_weather(document.city, document.country)
    if weather_data:
        document.weather_data = json.dumps(weather_data)
        document.weather_fetched_at = datetime.utcnow()
        document.status = "enriched"
        session.commit()
        return {
            "message": "Document enriched successfully",
            "weather": weather_data
        }
    else:
        document.status = "failed"
        session.commit()
        raise HTTPException(500, "Failed to enrich document with weather data")
# ============ WEATHER ENDPOINT ============
@app.get("/documents/{document_id}/weather")
@limiter.limit("10/minute")
def get_document_weather(
    request: Request,
    document_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Get the weather data associated with a document."""
    document = session.get(Document, document_id)
    if not document:
        raise HTTPException(404, "Document not found")
    if current_user.role not in ["admin", "manager"] and document.uploader_id != current_user.id:
        raise HTTPException(403, "Access denied")
    if not document.weather_data:
        raise HTTPException(404, "No weather data available for this document")
    return {
        "document_id": document.id,
        "city": document.city,
        "country": document.country,
        "weather": json.loads(document.weather_data)
    }
# ============ WEBHOOK ENDPOINTS (Exercise 3) ============
@app.post("/webhooks/register")
def register_webhook(
    webhook_data: WebhookCreate,
    current_user: User = Depends(get_current_admin),
    session: Session = Depends(get_session)
):
    """Register a webhook for document events."""
    webhook = Webhook(
        url=webhook_data.url,
        event_type=webhook_data.event_type,
        user_id=current_user.id
    )
    session.add(webhook)
    session.commit()
    session.refresh(webhook)
    return {
        "message": "Webhook registered successfully",
        "webhook_id": webhook.id,
        "event_type": webhook.event_type
    }
@app.get("/webhooks")
def list_webhooks(
    current_user: User = Depends(get_current_admin),
    session: Session = Depends(get_session)
):
    """List all registered webhooks."""
    webhooks = session.exec(select(Webhook)).all()
    return webhooks
@app.delete("/webhooks/{webhook_id}")
def delete_webhook(
    webhook_id: int,
    current_user: User = Depends(get_current_admin),
    session: Session = Depends(get_session)
):
    """Delete a webhook."""
    webhook = session.get(Webhook, webhook_id)
    if not webhook:
        raise HTTPException(404, "Webhook not found")
    session.delete(webhook)
    session.commit()
    return {"message": "Webhook deleted successfully"}
# ============ HEALTH ENDPOINT ============
@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "SendIt API"}
