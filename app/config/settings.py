"""Load and validate settings from environment variables."""

from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings. All values read from environment or .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # OpenAI (GPT-4o-mini)
    OPENAI_API_KEY: str = ""

    # Google Gemini (optional)
    GOOGLE_GEMINI_API_KEY: Optional[str] = None

    # Google OAuth (optional)
    GOOGLE_CLIENT_ID: Optional[str] = None
    GOOGLE_CLIENT_SECRET: Optional[str] = None

    # Google Custom Search (optional; used if SerpAPI not set)
    GOOGLE_API_KEY: Optional[str] = None
    GOOGLE_CSE_ID: Optional[str] = None

    # SerpAPI (web search – preferred when set)
    SERPAPI_API_KEY: Optional[str] = None

    # Qdrant (RAG)
    QDRANT_URL: Optional[str] = None
    QDRANT_API_KEY: Optional[str] = None


@lru_cache
def get_settings() -> Settings:
    """Cached settings instance."""
    return Settings()


# Singleton for direct import
settings = get_settings()
