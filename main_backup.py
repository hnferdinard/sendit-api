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
