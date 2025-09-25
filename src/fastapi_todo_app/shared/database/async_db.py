"""
Async database utilities and connection management
"""

from sqlalchemy.ext.asyncio import (
    create_async_engine, 
    AsyncSession, 
    async_sessionmaker
)
from sqlalchemy.pool import QueuePool
from contextlib import asynccontextmanager
import logging
from typing import AsyncGenerator, Optional
import os
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)


class AsyncDatabaseManager:
    """Async database connection manager with enhanced features"""
    
    def __init__(self, database_url: str, echo: bool = False):
        # Convert postgresql:// to postgresql+asyncpg://
        if database_url.startswith("postgresql://"):
            database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
        
        # Configure connection pool for optimal performance
        self.engine = create_async_engine(
            database_url,
            echo=echo or os.getenv("SQL_DEBUG", "false").lower() == "true",
            poolclass=QueuePool,
            pool_size=10,          # Number of connections to maintain
            max_overflow=20,       # Additional connections when pool is full
            pool_pre_ping=True,    # Validate connections before use
            pool_recycle=3600,     # Recycle connections every hour
        )
        
        # Create async session factory
        self.async_session_factory = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
    
    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get async database session with proper cleanup"""
        async with self.async_session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()
    
    def get_session_no_commit(self) -> AsyncSession:
        """Get async session without auto-commit (for manual transaction control)"""
        return self.async_session_factory()
    
    async def health_check(self) -> bool:
        """Check database connectivity"""
        try:
            async with self.get_session() as session:
                await session.execute("SELECT 1")
                return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False
    
    def get_pool_status(self) -> dict:
        """Get connection pool status"""
        pool = self.engine.pool
        return {
            "pool_size": pool.size(),
            "checked_in": pool.checkedin(),
            "checked_out": pool.checkedout(),
            "overflow": pool.overflow(),
            "invalid": pool.invalid(),
        }
    
    async def close(self):
        """Close database engine"""
        await self.engine.dispose()


# Database dependency injection
async def get_async_todos_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for getting todos database session"""
    if not todos_db:
        raise RuntimeError("Todos database not initialized")
    
    async with todos_db.get_session() as session:
        yield session


async def get_async_employees_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for getting employees database session"""
    if not employees_db:
        raise RuntimeError("Employees database not initialized")
    
    async with employees_db.get_session() as session:
        yield session


# Global database managers - to be initialized with actual URLs
todos_db: Optional[AsyncDatabaseManager] = None
employees_db: Optional[AsyncDatabaseManager] = None


async def initialize_databases(todos_url: str, employees_url: str):
    """Initialize both database managers"""
    global todos_db, employees_db
    
    todos_db = AsyncDatabaseManager(todos_url)
    employees_db = AsyncDatabaseManager(employees_url)
    
    # Verify connectivity
    todos_healthy = await todos_db.health_check()
    employees_healthy = await employees_db.health_check()
    
    if not todos_healthy:
        logger.error("Failed to connect to todos database")
    if not employees_healthy:
        logger.error("Failed to connect to employees database")
    
    logger.info(f"Databases initialized - Todos: {todos_healthy}, Employees: {employees_healthy}")


async def close_databases():
    """Close all database connections"""
    if todos_db:
        await todos_db.close()
    if employees_db:
        await employees_db.close()
    
    logger.info("Database connections closed")


# Legacy functions for backward compatibility
def create_async_database_engine(database_url: str):
    """Create an async database engine with optimized connection pooling"""
    return AsyncDatabaseManager(database_url).engine


def create_async_session_factory(engine):
    """Create an async session factory"""
    return async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False
    )


async def get_async_db_session(session_factory) -> AsyncGenerator[AsyncSession, None]:
    """Async database session dependency"""
    async with session_factory() as session:
        try:
            yield session
        finally:
            await session.close()