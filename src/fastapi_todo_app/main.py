"""
FastAPI TODO Application Entry Point
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.v1.api import api_router
from .core.config import settings
from .db.database import create_tables

# Create database tables on startup
create_tables()


def create_application() -> FastAPI:
    """
    Create and configure the FastAPI application.
    """
    app = FastAPI(
        title=settings.PROJECT_NAME,
        description="A TODO application built with FastAPI",
        version=settings.VERSION,
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # Set all CORS enabled origins
    if settings.BACKEND_CORS_ORIGINS:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    # Include API router
    app.include_router(api_router, prefix=settings.API_V1_STR)

    return app


app = create_application()


@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Welcome to FastAPI TODO App"}


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )