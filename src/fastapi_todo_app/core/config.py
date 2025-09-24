"""
Application configuration settings
"""

import os
from typing import Any, Dict, List, Optional, Union

from pydantic import AnyHttpUrl, field_validator, model_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables and .env file
    """

    model_config = {
        "extra": "ignore",  # Ignore extra fields from .env
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
    }

    PROJECT_NAME: str = "FastAPI TODO App"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"

    # Security
    SECRET_KEY: str = "your-secret-key-change-this-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days

    # CORS - Use str type to avoid JSON parsing issues
    BACKEND_CORS_ORIGINS: str = (
        "http://localhost:3000,http://localhost:8000,http://localhost:8080"
    )

    def get_cors_origins(self) -> List[str]:
        """Get CORS origins as a list"""
        if isinstance(self.BACKEND_CORS_ORIGINS, str):
            return [origin.strip() for origin in self.BACKEND_CORS_ORIGINS.split(",")]
        return self.BACKEND_CORS_ORIGINS

    # Database
    DATABASE_URL: Optional[str] = None
    SQLITE_DATABASE_URL: str = "sqlite:///./todo_app.db"

    @model_validator(mode="after")
    def get_database_url(self) -> "Settings":
        if not self.DATABASE_URL:
            self.DATABASE_URL = self.SQLITE_DATABASE_URL
        return self

    # Environment
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    # Logging
    LOG_LEVEL: str = "INFO"


settings = Settings()
