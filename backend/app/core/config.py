"""
Core application configuration.
"""
from functools import lru_cache
from pathlib import Path
from typing import Type, Tuple

from pydantic_settings import (
    BaseSettings, 
    SettingsConfigDict, 
    PydanticBaseSettingsSource
)
from langchain_google_genai import ChatGoogleGenerativeAI

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
ENV_FILE_PATH = BASE_DIR / ".env"

class Settings(BaseSettings):
    """Application settings."""

    APP_NAME: str = "Vacation Agent API"
    VERSION: str = "1.0.0"
    DEBUG: bool

    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    DATABASE_URL: str
    DB_MAX_CONNECTIONS: int
    SESSION_EXPIRY_DAYS: int = 30

    REDIS_HOST: str
    REDIS_PORT: int

    SMTP_HOST: str
    SMTP_PORT: int
    SMTP_USER: str
    SMTP_PASSWORD: str
    
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"

    WORKER_COUNT: int

    BACKEND_CORS_ORIGINS: list = ["http://localhost:5173", "http://127.0.0.1:5173"]

    GOOGLE_API_KEY: str
    SERPAPI_API_KEY: str
    RAPIDAPI_KEY: str
    OPENTRIPMAP_API_KEY: str

    LLM_MODEL: str = "gemini-2.5-flash"
    LLM_TEMPERATURE: float = 0.0
    
    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE_PATH),
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )
    
    @property
    def llm(self):
        """Get the configured LLM instance."""
        return ChatGoogleGenerativeAI(
            model=self.LLM_MODEL,
            max_retries=2,
            temperature=self.LLM_TEMPERATURE,
            api_key=self.GOOGLE_API_KEY
        )
    
    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: Type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> Tuple[PydanticBaseSettingsSource, ...]:
        return (init_settings, dotenv_settings, env_settings, file_secret_settings)


@lru_cache
def get_settings() -> Settings:
    return Settings()

settings = get_settings()