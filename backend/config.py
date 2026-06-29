from dotenv import load_dotenv
import os

load_dotenv() # Reads .env file and loads env variables, securing secrets and API keys
#Every file in the project will import from config.py. Nothing will ever call os.getenv() directly or hardcode a value. 

class Settings:
    JWT_SECRET: str = os.getenv("JWT_SECRET")
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_MINUTES: int = 30
    DATABASE_URL: str = os.getenv("DATABASE_URL")

    def __init__(self):
        if not self.JWT_SECRET:
            raise ValueError("JWT_SECRET is not set in .env")
        if not self.DATABASE_URL:
            raise ValueError("DATABASE_URL is not set in .env")

settings = Settings()