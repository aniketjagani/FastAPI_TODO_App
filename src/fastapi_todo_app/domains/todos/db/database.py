"""
Database configuration and session management for TODO domain (PostgreSQL)
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from typing import Generator
from urllib.parse import quote_plus
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# PostgreSQL Database URL for TODOs
# Use a separate database or schema for TODOs
TODO_DATABASE_URL = os.getenv("TODO_DATABASE_URL")

# If not set, build from individual components
if not TODO_DATABASE_URL:
    POSTGRES_USER = os.getenv("POSTGRES_USER", "aniketjagani")
    POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "adminaniket")
    POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
    POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
    TODO_DB = os.getenv("TODO_DB", "todos_db")  # Separate database for TODOs

    # URL encode password to handle special characters
    encoded_password = quote_plus(POSTGRES_PASSWORD)
    TODO_DATABASE_URL = f"postgresql://{POSTGRES_USER}:{encoded_password}@{POSTGRES_HOST}:{POSTGRES_PORT}/{TODO_DB}"

# Create PostgreSQL engine with connection pooling
engine = create_engine(
    TODO_DATABASE_URL,
    poolclass=QueuePool,
    pool_size=5,  # Smaller pool for TODOs
    max_overflow=10,
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=os.getenv("SQL_DEBUG", "false").lower() == "true",
)

# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create Base class for models
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """
    Dependency that provides a database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    """
    Create all tables in the database
    """
    Base.metadata.create_all(bind=engine)