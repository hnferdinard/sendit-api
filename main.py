from fastapi import FastAPI, HTTPException, Depends, Form
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
import os
import uvicorn
from typing import Optional
from fastapi.encoders import jsonable_encoder
app = FastAPI(title="SendIt API", version="1.0.0")
# Models
class UserRegister(BaseModel):
    username: str
    email: str
    password: str
    full_name: str
    role: str = "staff"
class UserLogin(BaseModel):
    username: str
    password: str
# In-memory storage
users_db = {}
tokens_db = {}
@app.get("/")
@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "SendIt API",
        "version": "1.0.0"
    }
@app.post("/register")
def register(user: UserRegister):
    if user.username in users_db:
        raise HTTPException(400, "Username already exists")
    users_db[user.username] = user.dict()
    return {
        "message": "User registered successfully",
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
    # Check if JSON data was sent
    if user_data:
        username = user_data.username
        password = user_data.password
    # If no data provided, try to get from form
    if not username and not password:
        raise HTTPException(400, "Username and password required")
    if username not in users_db:
        raise HTTPException(401, "Invalid credentials")
    if users_db[username]["password"] != password:
        raise HTTPException(401, "Invalid credentials")
    token = f"token-{username}-{os.urandom(8).hex()}"
    tokens_db[token] = username
    return {
        "access_token": token,
        "token_type": "bearer"
    }
@app.get("/documents")
def list_documents():
    return {
        "message": "Documents endpoint - working!",
        "documents": []
    }
if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
