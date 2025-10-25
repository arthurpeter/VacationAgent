"""
Core application configuration.
"""
from typing import Optional
from pydantic_settings import BaseSettings
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    """Application settings."""
    
    # App
    APP_NAME: str = "Vacation Agent API"
    VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # Database
    DATABASE_URL: str = "sqlite:///./mydatabase.db"
    SESSION_EXPIRY_DAYS: int = 30
    
    JWT_SECRET_KEY: str = "your_secret_key"
    JWT_ALGORITHM: str = "HS256"

    # CORS
    BACKEND_CORS_ORIGINS: list = ["http://localhost:5173", "http://127.0.0.1:5173"]
    
    # External APIs
    OPENAI_API_KEY: Optional[str] = None
    GOOGLE_API_KEY: Optional[str] = None
    SERPAPI_API_KEY: Optional[str] = None
    
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
        env_file = ".env"
        case_sensitive = True


settings = Settings()
