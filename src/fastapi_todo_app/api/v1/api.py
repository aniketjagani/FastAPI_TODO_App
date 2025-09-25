"""
API v1 router aggregation with health checks
"""

from fastapi import APIRouter

from ...domains.todos.api import todos_router
from ...domains.employees.api import employees_router
from .health import router as health_router

api_router = APIRouter()

# Domain routers
api_router.include_router(todos_router, prefix="/todos", tags=["todos"])
api_router.include_router(employees_router, prefix="/employees", tags=["employees"])

# Health check endpoints
api_router.include_router(health_router, tags=["health"])
