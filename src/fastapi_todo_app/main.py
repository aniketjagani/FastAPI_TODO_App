"""
Enhanced FastAPI TODO Application Entry Point with Optimizations
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
import time
import logging
import os

from .api.v1.api import api_router
from .shared.core.config import settings
from .domains.todos.db.database import (
    create_tables as create_todo_tables,
)  # PostgreSQL for TODOs
from .domains.employees.db.database import (
    create_tables as create_employee_tables,
)  # PostgreSQL for Employees
from .domains.todos.schemas.todo import TodoStats

# Import new optimization features
from .shared.database.async_db import initialize_databases, close_databases
from .shared.utils.caching import cache_service
from .shared.utils.rate_limiting import rate_limit_service

# Configure enhanced logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        (
            logging.FileHandler("app.log")
            if settings.LOG_TO_FILE
            else logging.NullHandler()
        ),
    ],
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan handler for startup and shutdown events
    """
    # Startup
    logger.info("🚀 Starting FastAPI TODO & Employee Application with optimizations")
    try:
        # Create PostgreSQL tables for TODOs
        create_todo_tables()
        logger.info("✅ PostgreSQL TODO tables created successfully")

        # Create PostgreSQL tables for Employees
        create_employee_tables()
        logger.info("✅ PostgreSQL Employee tables created successfully")

        # Initialize async database connections
        todos_db_url = os.getenv("TODOS_DATABASE_URL")
        employees_db_url = os.getenv("EMPLOYEES_DATABASE_URL")

        if todos_db_url and employees_db_url:
            await initialize_databases(todos_db_url, employees_db_url)
            logger.info("✅ Async database connections initialized")
        else:
            logger.warning(
                "⚠️ Async database URLs not configured, using sync connections"
            )

        # Initialize cache service with Redis if available
        redis_url = os.getenv("REDIS_URL")
        if redis_url:
            cache_service.__init__(redis_url=redis_url)
            logger.info("✅ Redis cache initialized")
        else:
            logger.warning("⚠️ Redis URL not configured, using in-memory cache")

    except Exception as e:
        logger.error(f"❌ Error during application startup: {e}")
        raise

    yield

    # Shutdown
    logger.info("👋 Shutting down FastAPI TODO Application")
    try:
        await close_databases()
        logger.info("✅ Database connections closed")
    except Exception as e:
        logger.error(f"❌ Error during shutdown: {e}")


def create_application() -> FastAPI:
    """
    Create and configure the enhanced FastAPI application with Pydantic integration.
    """
    app = FastAPI(
        title="FastAPI TODO & Employee Management System",
        description="""
        ## Enhanced TODO & Employee Management with Pydantic Models 🚀
        
        A comprehensive dual-application system built with:
        - **FastAPI** for high-performance APIs
        - **Pydantic V2** for data validation and serialization
        - **SQLAlchemy** for database operations
        - **PostgreSQL** for employee data
        - **SQLite** for TODO data
        - **UV** for modern Python package management
        
        ### TODO Features:
        - ✅ Full CRUD operations for todos
        - 🏷️ Advanced filtering and search
        - 📊 Statistics and analytics
        - 🎯 Priority and status management  
        - 📅 Due date tracking
        - 🏷️ Tag-based organization
        - 📦 Bulk operations

        ### Employee Features:
        - 👥 Complete employee management
        - 🏢 Department-based organization
        - 💰 Salary and compensation tracking
        - 📈 Employment status management
        - 👨‍💼 Manager-employee relationships
        - 🔍 Advanced search and filtering
        - 📊 Employee statistics and analytics
        
        ### API Documentation:
        - **Swagger UI**: Available at `/docs`
        - **ReDoc**: Available at `/redoc`
        """,
        version=settings.VERSION,
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # Add security middleware
    if settings.ENVIRONMENT == "production":
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=["localhost", "127.0.0.1", "*.herokuapp.com"],
        )

    # Add timing middleware for performance monitoring
    @app.middleware("http")
    async def add_process_time_header(request: Request, call_next):
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(process_time)
        return response

    # Set CORS middleware
    if settings.BACKEND_CORS_ORIGINS:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.get_cors_origins(),
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    # Custom exception handlers for better error messages
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ):
        """Handle Pydantic validation errors"""
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "detail": "Validation Error",
                "errors": exc.errors(),
                "message": "Please check your request data and try again.",
            },
        )

    @app.exception_handler(ValidationError)
    async def pydantic_validation_exception_handler(
        request: Request, exc: ValidationError
    ):
        """Handle Pydantic model validation errors"""
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "detail": "Pydantic Validation Error",
                "errors": exc.errors(),
                "message": "Data validation failed.",
            },
        )

    # Include API router
    app.include_router(api_router, prefix=settings.API_V1_STR)

    return app


app = create_application()


@app.get("/", tags=["Root"])
async def root():
    """
    Root endpoint with enhanced information about the Pydantic-powered API
    """
    return {
        "message": "🚀 Welcome to Enhanced FastAPI TODO App with Pydantic Models!",
        "version": settings.VERSION,
        "docs": "/docs",
        "redoc": "/redoc",
        "api_base": settings.API_V1_STR,
        "features": [
            "Pydantic data validation",
            "Advanced filtering",
            "Statistics dashboard",
            "Bulk operations",
            "Priority management",
            "Tag-based organization",
        ],
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """
    Enhanced health check endpoint with system information
    """
    from datetime import datetime

    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "pydantic_enabled": True,
        "database": "connected" if settings.DATABASE_URL else "not configured",
    }


@app.get("/info", tags=["System"])
async def app_info():
    """
    Application information endpoint showcasing Pydantic integration
    """
    return {
        "application": {
            "name": settings.PROJECT_NAME,
            "version": settings.VERSION,
            "environment": settings.ENVIRONMENT,
        },
        "technology_stack": {
            "framework": "FastAPI",
            "validation": "Pydantic V2",
            "database": "SQLAlchemy + SQLite/PostgreSQL",
            "package_manager": "UV",
        },
        "pydantic_models": {
            "TodoCreate": "Enhanced todo creation with validation",
            "TodoUpdate": "Flexible todo updates",
            "TodoResponse": "Comprehensive todo data",
            "TodoFilter": "Advanced filtering capabilities",
            "TodoStats": "Analytics and statistics",
            "TodoStatus": "Status management enum",
            "TodoPriority": "Priority level enum",
        },
        "api_endpoints": f"{settings.API_V1_STR}/todos/",
        "documentation": {
            "swagger": "/docs",
            "redoc": "/redoc",
            "openapi": f"{settings.API_V1_STR}/openapi.json",
        },
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "fastapi_todo_app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level=settings.LOG_LEVEL.lower(),
    )
