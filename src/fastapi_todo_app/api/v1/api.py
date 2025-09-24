"""
API v1 router aggregation
"""

from fastapi import APIRouter

from . import todos
from ...employees.api import employees_router

api_router = APIRouter()

api_router.include_router(todos.router, prefix="/todos", tags=["todos"])
api_router.include_router(employees_router, prefix="/employees", tags=["employees"])
