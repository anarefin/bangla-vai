import os
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

class Settings:
    """Application settings and configuration"""
    
    # API Keys
    ELEVENLABS_API_KEY: Optional[str] = os.getenv("ELEVENLABS_API_KEY")
    GOOGLE_API_KEY: Optional[str] = os.getenv("GOOGLE_API_KEY")
    
    # Database Configuration
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./data/databases/sqlite/tickets.db")
    
    # File Storage Paths
    VOICES_DIR: str = os.getenv("VOICES_DIR", "./data/uploads/voices")
    ATTACHMENTS_DIR: str = os.getenv("ATTACHMENTS_DIR", "./data/uploads/attachments")
    
    # ChromaDB Configuration
    CHROMA_DB_PATH: str = os.getenv("CHROMA_DB_PATH", "./data/databases/chroma")
    
    # API Configuration
    FASTAPI_HOST: str = os.getenv("FASTAPI_HOST", "0.0.0.0")
    FASTAPI_PORT: int = int(os.getenv("FASTAPI_PORT", "8000"))
    STREAMLIT_PORT: int = int(os.getenv("STREAMLIT_PORT", "8501"))
    
    # Application Settings
    APP_NAME: str = "Bangla Vai Ticketing System"
    APP_VERSION: str = "2.0.0"
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    
    # CORS Settings
    CORS_ORIGINS: list = ["*"]  # In production, specify actual origins
    
    # File Upload Settings
    MAX_FILE_SIZE: int = 50 * 1024 * 1024  # 50MB
    ALLOWED_AUDIO_EXTENSIONS: list = [".wav", ".mp3", ".ogg", ".m4a", ".webm"]
    ALLOWED_ATTACHMENT_EXTENSIONS: list = [".pdf", ".doc", ".docx", ".txt", ".png", ".jpg", ".jpeg", ".gif"]

settings = Settings() 