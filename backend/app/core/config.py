"""
Application configuration using pydantic-settings
"""
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # Application
    APP_NAME: str = "Code-Monitor"
    APP_ENV: str = "development"
    DEBUG: bool = True
    API_PORT: int = 8000

    # Database
    DATABASE_URL: str = "postgresql://lab:lab123@localhost:5433/code_monitor"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Git
    GIT_CLONE_DIR: str = "/tmp/repos"

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # Ignore extra fields in .env not defined in Settings


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()
