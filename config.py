import os
from pathlib import Path
# Database configuration
DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/sendit_db"
# Security
SECRET_KEY = "your-super-secret-key-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
# Weather API
WEATHER_API_KEY = "your-api-key"
WEATHER_API_URL = "https://api.open-meteo.com/v1/forecast"
# File upload limits
MAX_UPLOAD_SIZE = 5242880  # 5 MB
