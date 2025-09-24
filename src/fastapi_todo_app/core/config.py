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
    
    PROJECT_NAME: str = "FastAPI TODO App"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Security
    SECRET_KEY: str = "your-secret-key-change-this-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days
    
    # CORS
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = [
        "http://localhost:3000",  # React default
        "http://localhost:8000",  # FastAPI default
        "http://localhost:8080",  # Vue default
    ]
    
    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)
    
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
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


settings = Settings()