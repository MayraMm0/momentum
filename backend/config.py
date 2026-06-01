from dotenv import load_dotenv
import os

load_dotenv() # Reads .env file and loads env variables, securing secrets and API keys
#Every file in the project will import from config.py. Nothing will ever call os.getenv() directly or hardcode a value. 

JWT_SECRET = os.getenv("JWT_SECRET")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_MINUTES = 30
DATABASE_URL = os.getenv("DATABASE_URL")

# Fail at startup if critical secrets are missing
if not JWT_SECRET:
    raise ValueError("JWT_SECRET is not set in .env")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL is not set in .env")