import os

from pydantic import BaseModel
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV_FILE_PATH = os.path.join(BASE_DIR, ".env")

print("="*50)
print(f"[DEBUG] Looking for .env file at: {ENV_FILE_PATH}")
print(f"[DEBUG] Does file exist? {os.path.exists(ENV_FILE_PATH)}")
print("="*50)

load_dotenv(ENV_FILE_PATH)

class Settings(BaseSettings):
    PROJECT_NAME: str = "PULSE"
    
    # Qdrant cloud settings
    QDRANT_URL: str = "http://localhost:6333"
    QDRANT_API_KEY: str | None = None
    COLLECTION_NAME: str = "pulse_intel"
    VECTOR_SIZE: int = 384
    
    # Cloud LLM Settings
    LLM_BASE_URL: str = "http://localhost:11434/api/chat"
    LLM_MODEL: str = "phi3:mini" 
    LLM_API_KEY: str
    
    # email settings
    SMTP_USERNAME: str | None = None
    USER_EMAIL: str | None = None
    SMTP_SERVER: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_PASSWORD: str | None = None
    
    ENCRYPTION_MASTER_KEY: str
    
    DATABASE_URL: str
    
    JWT_SECRET_KEY: str
    

settings = Settings()

print("="*50)
print(f"[SYSTEM BOOT] Database URL: {settings.QDRANT_URL}")
print(f"[SYSTEM BOOT] AI Brain URL: {settings.LLM_BASE_URL}")
print("="*50)