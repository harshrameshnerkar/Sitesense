"""
Core Configuration Module for SiteSense.
Loads and validates settings from environment variables and .env file.
"""

from functools import lru_cache
from pathlib import Path
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Application Info
    APP_NAME: str = "SiteSense"
    APP_ENV: str = "development"
    DEBUG: bool = True
    API_V1_STR: str = "/api/v1"
    
    # Security
    SECRET_KEY: str = "sitesense-dev-secret-key-32-characters-minimum-secure"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    ALGORITHM: str = "HS256"

    # Database
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/sitesense"
    DATABASE_FALLBACK_SQLITE: bool = True
    
    # Storage Directories
    STORAGE_DIR: str = "./storage"
    UPLOAD_DIR: str = "./storage/uploads"
    ANNOTATED_DIR: str = "./storage/annotated"
    REPORT_DIR: str = "./storage/reports"

    # Multimodal Models
    VISION_MODEL_NAME: str = "google/owlvit-base-patch32"
    EMBEDDING_MODEL_NAME: str = "all-MiniLM-L6-v2"
    GEMINI_API_KEY: str = ""
    OPENAI_API_KEY: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @field_validator("DEBUG", mode="before")
    def parse_debug(cls, v):
        if isinstance(v, str):
            return v.lower() in ("true", "1", "t", "yes", "y", "debug")
        return bool(v)

    def ensure_directories(self) -> None:
        """Create storage directories if they do not exist."""
        for path_str in [self.STORAGE_DIR, self.UPLOAD_DIR, self.ANNOTATED_DIR, self.REPORT_DIR]:
            path = Path(path_str)
            path.mkdir(parents=True, exist_ok=True)


@lru_cache()
def get_settings() -> Settings:
    """Return cached settings instance."""
    settings = Settings()
    settings.ensure_directories()
    return settings
