"""
PostgreSQL Database Configuration for Employees App
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
from urllib.parse import quote_plus
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# PostgreSQL Database URL
DATABASE_URL = os.getenv("POSTGRES_DATABASE_URL")

# If not set, build from individual components with proper encoding
if not DATABASE_URL:
    POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
    POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "password")
    POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
    POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
    POSTGRES_DB = os.getenv("POSTGRES_DB", "employees_db")
    
    # URL encode password to handle special characters
    encoded_password = quote_plus(POSTGRES_PASSWORD)
    DATABASE_URL = f"postgresql://{POSTGRES_USER}:{encoded_password}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"

# Create PostgreSQL engine with connection pooling
engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,  # Verify connections before use
    pool_recycle=3600,   # Recycle connections after 1 hour
    echo=os.getenv("SQL_DEBUG", "false").lower() == "true"  # SQL logging
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for SQLAlchemy models
Base = declarative_base()


def get_db():
    """
    Dependency to get database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    """
    Create all database tables
    """
    Base.metadata.create_all(bind=engine)


def drop_tables():
    """
    Drop all database tables (use with caution!)
    """
    Base.metadata.drop_all(bind=engine)


def get_database_info():
    """
    Get database connection information
    """
    return {
        "database_url": DATABASE_URL.replace(DATABASE_URL.split('@')[0].split('//')[-1] + '@', '***@'),
        "driver": engine.driver,
        "pool_size": engine.pool.size(),
        "checked_out": engine.pool.checkedout(),
        "overflow": engine.pool.overflow(),
    }