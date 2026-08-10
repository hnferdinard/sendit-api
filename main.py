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
    description="📄 Document Management & Enrichment Service with Weather Integration"
)
# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")
# Custom CSS for Swagger UI
custom_css = """
<style>
    /* Background for the entire page */
    body {
        background-image: url('/static/background.jpg');
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
        background-repeat: no-repeat;
    }
    /* Background for Swagger UI container */
    .swagger-ui {
        background: rgba(255, 255, 255, 0.92);
        border-radius: 15px;
        padding: 20px;
        margin: 20px;
        backdrop-filter: blur(10px);
        box-shadow: 0 8px 32px rgba(0,0,0,0.3);
    }
    /* Header styling */
    .swagger-ui .topbar {
        background: rgba(0, 0, 0, 0.7) !important;
        border-radius: 10px 10px 0 0;
        padding: 15px !important;
    }
    .swagger-ui .topbar .download-url-wrapper .select-label {
        color: #fff !important;
    }
    /* Info section */
    .swagger-ui .info .title {
        color: #1a1a2e !important;
        text-shadow: 2px 2px 4px rgba(255,255,255,0.5);
    }
    /* Buttons */
    .swagger-ui .btn {
        border-radius: 8px !important;
        font-weight: bold !important;
    }
    .swagger-ui .btn.execute {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        color: white !important;
        border: none !important;
    }
    .swagger-ui .btn.execute:hover {
        transform: scale(1.05);
        transition: all 0.3s ease;
    }
    /* Try it out button */
    .swagger-ui .btn.try-out__btn {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%) !important;
        color: white !important;
        border: none !important;
    }
    /* Response section */
    .swagger-ui .responses-wrapper {
        background: rgba(255, 255, 255, 0.9);
        border-radius: 10px;
        padding: 10px;
    }
    /* Table styling */
    .swagger-ui .model-box {
        background: rgba(255, 255, 255, 0.9);
        border-radius: 8px;
    }
    /* Custom footer */
    .custom-footer {
        text-align: center;
        padding: 20px;
        color: #fff;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.8);
        font-size: 14px;
        background: rgba(0,0,0,0.4);
        border-radius: 10px;
        margin: 20px;
        backdrop-filter: blur(5px);
    }
</style>
'''
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
    # Add custom CSS
    html.body = html.body.replace(
        '</head>',
        f'{custom_css}</head>'
    )
    return html
# ============ YOUR EXISTING CODE HERE ============
# (All your endpoints - register, login, upload, etc.)
# ... keep all your existing endpoints ...
# ============ HEALTH CHECK ============
@app.get("/")
@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "SendIt API",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat(),
        "uptime": "🚀 Live on Render!",
        "message": "📄 Document Management & Enrichment Service"
    }
# ============ CUSTOM HTML PAGE ============
@app.get("/home", response_class=HTMLResponse)
async def home():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>SendIt API</title>
        <style>
            body {
                margin: 0;
                padding: 0;
                background-image: url('/static/background.jpg');
                background-size: cover;
                background-position: center;
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                height: 100vh;
                display: flex;
                justify-content: center;
                align-items: center;
            }
            .container {
                background: rgba(255, 255, 255, 0.9);
                padding: 50px;
                border-radius: 20px;
                text-align: center;
                backdrop-filter: blur(10px);
                box-shadow: 0 8px 32px rgba(0,0,0,0.3);
                max-width: 600px;
            }
            h1 {
                color: #1a1a2e;
                font-size: 3em;
                margin-bottom: 10px;
            }
            p {
                color: #2d3436;
                font-size: 1.2em;
                line-height: 1.6;
            }
            .btn {
                display: inline-block;
                padding: 12px 30px;
                margin: 10px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                text-decoration: none;
                border-radius: 30px;
                font-weight: bold;
                transition: transform 0.3s;
            }
            .btn:hover {
                transform: scale(1.05);
            }
            .features {
                text-align: left;
                margin: 20px 0;
            }
            .features li {
                padding: 5px 0;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>📄 SendIt API</h1>
            <p>Document Management & Enrichment Service</p>
            <div class="features">
                <ul style="list-style: none; padding: 0;">
                    <li>✅ Upload & Manage Documents</li>
                    <li>✅ Weather Data Enrichment</li>
                    <li>✅ Document Search & Versioning</li>
                    <li>✅ Webhook Notifications</li>
                </ul>
            </div>
            <a href="/docs" class="btn">📚 API Documentation</a>
            <a href="/health" class="btn" style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);">❤️ Health Check</a>
            <p style="margin-top: 20px; font-size: 0.9em; color: #636e72;">
                Powered by FastAPI 🚀
            </p>
        </div>
    </body>
    </html>
    """
# ... keep all your other endpoints (register, login, documents, webhooks, etc.) ...
