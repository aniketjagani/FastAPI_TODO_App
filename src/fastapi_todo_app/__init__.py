"""
FastAPI TODO Application Package
"""

__version__ = "0.1.0"


def main() -> None:
    """Main entry point for the application"""
    import uvicorn
    
    uvicorn.run(
        "fastapi_todo_app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
