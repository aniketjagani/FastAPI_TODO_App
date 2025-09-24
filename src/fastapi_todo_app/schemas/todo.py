"""
Pydantic schemas for request/response models
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class TodoBase(BaseModel):
    """Base schema for Todo"""
    title: str
    description: Optional[str] = None
    completed: bool = False


class TodoCreate(TodoBase):
    """Schema for creating a new Todo"""
    pass


class TodoUpdate(BaseModel):
    """Schema for updating an existing Todo"""
    title: Optional[str] = None
    description: Optional[str] = None
    completed: Optional[bool] = None


class TodoResponse(TodoBase):
    """Schema for Todo response"""
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class TodoList(BaseModel):
    """Schema for Todo list response"""
    todos: list[TodoResponse]
    total: int
    page: int
    size: int