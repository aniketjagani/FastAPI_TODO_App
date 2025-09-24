"""
Shared database utilities and base classes
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
from urllib.parse import quote_plus
import os
from typing import Generator
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Create Base class for all models
Base = declarative_base()


def create_database_engine(database_url: str, pool_size: int = 5, max_overflow: int = 10):
    """Create a database engine with connection pooling"""
    return create_engine(
        database_url,
        poolclass=QueuePool,
        pool_size=pool_size,
        max_overflow=max_overflow,
        pool_pre_ping=True,
        pool_recycle=3600,
        echo=os.getenv("SQL_DEBUG", "false").lower() == "true",
    )


def create_session_factory(engine):
    """Create a session factory for the given engine"""
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)


def build_postgres_url(user: str, password: str, host: str, port: str, database: str) -> str:
    """Build PostgreSQL connection URL with proper encoding"""
    encoded_password = quote_plus(password)
    return f"postgresql://{user}:{encoded_password}@{host}:{port}/{database}"