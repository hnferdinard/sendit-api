from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
import os
import uvicorn
# Simple app without complex dependencies for Render
app = FastAPI(title="SendIt API", version="1.0.0")
# Simple models
class UserRegister(BaseModel):
    username: str
    email: str
    password: str
    full_name: str
    role: str = "staff"
# Store users in memory (for Render demo)
users_db = {}
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
def login(username: str, password: str):
    if username not in users_db:
        raise HTTPException(401, "Invalid credentials")
    if users_db[username]["password"] != password:
        raise HTTPException(401, "Invalid credentials")
    return {
        "access_token": f"fake-token-{username}",
        "token_type": "bearer"
    }
@app.get("/documents")
def list_documents():
    return {"message": "Documents endpoint - working!"}
if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
