"""
API v1 router aggregation
"""

from fastapi import APIRouter

from . import todos

api_router = APIRouter()

api_router.include_router(todos.router, prefix="/todos", tags=["todos"])