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
    LOG_TO_FILE: bool = False

    # Cache settings
    REDIS_URL: Optional[str] = None
    CACHE_DEFAULT_TTL: int = 300

    # Rate limiting
    RATE_LIMIT_PER_MINUTE: int = 100
    USER_RATE_LIMIT_PER_MINUTE: int = 1000

    # Monitoring
    ENABLE_METRICS: bool = True
    SLOW_QUERY_THRESHOLD: float = 1.0
    ENABLE_TRACING: bool = False

    # Advanced Features
    ENABLE_AUTHENTICATION: bool = True
    ENABLE_API_KEYS: bool = True
    JWT_SECRET_KEY: str = "jwt-secret-key-change-this-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Export/Import
    MAX_EXPORT_RECORDS: int = 100000
    EXPORT_FILE_TTL_HOURS: int = 24

    # Search Configuration
    ENABLE_FUZZY_SEARCH: bool = True
    SEARCH_RESULTS_LIMIT: int = 1000

    # Bulk Operations
    MAX_BULK_OPERATIONS: int = 1000
    BULK_OPERATION_TIMEOUT: int = 300  # 5 minutes

    # Security Settings
    PASSWORD_MIN_LENGTH: int = 8
    MAX_LOGIN_ATTEMPTS: int = 5
    ACCOUNT_LOCKOUT_DURATION: int = 900  # 15 minutes

    # Performance Settings
    MAX_CONCURRENT_REQUESTS: int = 100
    REQUEST_TIMEOUT: int = 30

    # Feature Flags
    FEATURE_ADVANCED_ANALYTICS: bool = True
    FEATURE_EXPORT_IMPORT: bool = True
    FEATURE_BULK_OPERATIONS: bool = True

    # Application naming for better organization
    APP_NAME: str = "FastAPI TODO & Employee Management System"


settings = Settings()
