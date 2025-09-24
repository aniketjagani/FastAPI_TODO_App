"""
API v1 router aggregation
"""

from fastapi import APIRouter

from ...domains.todos.api import todos_router
from ...domains.employees.api import employees_router

api_router = APIRouter()

api_router.include_router(todos_router, prefix="/todos", tags=["todos"])
api_router.include_router(employees_router, prefix="/employees", tags=["employees"])
