"""
Core application configuration.
"""
import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv

ROOT_ENV = Path(__file__).resolve().parents[3] / ".env"
load_dotenv(ROOT_ENV)

class Settings(BaseSettings):
    """Application settings."""
    
    # App
    APP_NAME: str = "Vacation Agent API"
    VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL")
    SESSION_EXPIRY_DAYS: int = 30

    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", 6379))

    SMTP_HOST: str = os.getenv("SMTP_HOST", "smtp.gmail.com")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", 587))
    SMTP_USER: Optional[str] = os.getenv("SMTP_USER")
    SMTP_PASSWORD: Optional[str] = os.getenv("SMTP_PASSWORD")
    
    JWT_SECRET_KEY: str = "your_secret_key"
    JWT_ALGORITHM: str = "HS256"

    # CORS
    BACKEND_CORS_ORIGINS: list = ["http://localhost:5173", "http://127.0.0.1:5173"]
    
    # External APIs
    OPENAI_API_KEY: Optional[str] = None
    GOOGLE_API_KEY: Optional[str] = None
    SERPAPI_API_KEY: Optional[str] = None
    RAPIDAPI_KEY: Optional[str] = None

    # Other env variables
    POSTGRES_USER: Optional[str] = None
    POSTGRES_PASSWORD: Optional[str] = None
    POSTGRES_DB: Optional[str] = None
    DATABASE_URL: Optional[str] = None
    REDIS_HOST: Optional[str] = None
    REDIS_PORT: Optional[int] = None
    
    # LLM Configuration
    LLM_MODEL: str = "gemini-2.0-flash"
    LLM_TEMPERATURE: float = 0.0
    
    @property
    def llm(self):
        """Get the configured LLM instance."""
        return ChatGoogleGenerativeAI(
            model=self.LLM_MODEL, 
            temperature=self.LLM_TEMPERATURE
        )
    
    class Config:
        env_file = str(ROOT_ENV)
        case_sensitive = True


settings = Settings()
