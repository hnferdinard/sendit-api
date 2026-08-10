from dotenv import load_dotenv
import os
load_dotenv()
print("DATABASE_URL:", os.getenv("DATABASE_URL"))
print("SECRET_KEY:", os.getenv("SECRET_KEY"))
print("ALL ENV VARIABLES:")
for key, value in os.environ.items():
    if "DATABASE" in key or "SECRET" in key:
        print(f"{key}: {value}")
