"""
Enhanced Pydantic models for Todo application with comprehensive validation
"""

from datetime import datetime
from enum import Enum
from typing import Optional, List
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class TodoStatus(str, Enum):
    """Enum for Todo status"""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class TodoPriority(str, Enum):
    """Enum for Todo priority"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class TodoBase(BaseModel):
    """Base Pydantic model for Todo with validation"""
    title: str = Field(
        ..., min_length=1, max_length=200, description="Title of the todo item"
    )
    description: Optional[str] = Field(
        None, max_length=1000, description="Detailed description of the todo item"
    )
    completed: bool = Field(
        default=False, description="Whether the todo item is completed"
    )
    priority: TodoPriority = Field(
        default=TodoPriority.MEDIUM, description="Priority level of the todo item"
    )
    status: TodoStatus = Field(
        default=TodoStatus.PENDING, description="Current status of the todo item"
    )
    due_date: Optional[datetime] = Field(None, description="Due date for the todo item")
    tags: List[str] = Field(
        default_factory=list, description="Tags associated with the todo item"
    )

    @field_validator("title")
    @classmethod
    def validate_title(cls, v: str) -> str:
        """Validate and clean title"""
        if not v or not v.strip():
            raise ValueError("Title cannot be empty or just whitespace")
        return v.strip()

    @field_validator("description")
    @classmethod
    def validate_description(cls, v: Optional[str]) -> Optional[str]:
        """Validate and clean description"""
        if v is not None:
            v = v.strip()
            return v if v else None
        return v

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, v: List[str]) -> List[str]:
        """Validate and clean tags"""
        if not v:
            return []
        # Remove duplicates and empty tags, strip whitespace
        cleaned_tags = []
        seen = set()
        for tag in v:
            if isinstance(tag, str):
                cleaned_tag = tag.strip().lower()
                if cleaned_tag and cleaned_tag not in seen:
                    cleaned_tags.append(cleaned_tag)
                    seen.add(cleaned_tag)
        return cleaned_tags

    @model_validator(mode="after")
    def validate_completion_status(self):
        """Ensure completed status matches status field"""
        if self.completed and self.status not in [
            TodoStatus.COMPLETED,
            TodoStatus.CANCELLED,
        ]:
            self.status = TodoStatus.COMPLETED
        elif not self.completed and self.status == TodoStatus.COMPLETED:
            self.completed = True
        return self


class TodoCreate(TodoBase):
    """Pydantic model for creating a new Todo"""

    @model_validator(mode="after")
    def validate_create_data(self):
        """Additional validation for todo creation"""
        if self.due_date and self.due_date < datetime.now():
            raise ValueError("Due date cannot be in the past")
        return self


class TodoUpdate(BaseModel):
    """Pydantic model for updating an existing Todo"""
    title: Optional[str] = Field(
        None, min_length=1, max_length=200, description="Updated title of the todo item"
    )
    description: Optional[str] = Field(
        None, max_length=1000, description="Updated description of the todo item"
    )
    completed: Optional[bool] = Field(None, description="Updated completion status")
    priority: Optional[TodoPriority] = Field(None, description="Updated priority level")
    status: Optional[TodoStatus] = Field(None, description="Updated status")
    due_date: Optional[datetime] = Field(None, description="Updated due date")
    tags: Optional[List[str]] = Field(None, description="Updated tags list")

    @field_validator("title")
    @classmethod
    def validate_title(cls, v: Optional[str]) -> Optional[str]:
        """Validate title if provided"""
        if v is not None:
            if not v or not v.strip():
                raise ValueError("Title cannot be empty or just whitespace")
            return v.strip()
        return v

    @field_validator("description")
    @classmethod
    def validate_description(cls, v: Optional[str]) -> Optional[str]:
        """Validate description if provided"""
        if v is not None:
            v = v.strip()
            return v if v else None
        return v

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        """Validate tags if provided"""
        if v is not None:
            # Remove duplicates and empty tags, strip whitespace
            cleaned_tags = []
            seen = set()
            for tag in v:
                if isinstance(tag, str):
                    cleaned_tag = tag.strip().lower()
                    if cleaned_tag and cleaned_tag not in seen:
                        cleaned_tags.append(cleaned_tag)
                        seen.add(cleaned_tag)
            return cleaned_tags
        return v


class TodoResponse(TodoBase):
    """Pydantic model for Todo response"""
    id: int = Field(..., description="Unique identifier for the todo item")
    created_at: datetime = Field(..., description="Timestamp when the todo was created")
    updated_at: Optional[datetime] = Field(
        None, description="Timestamp when the todo was last updated"
    )

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "title": "Complete FastAPI project",
                "description": "Implement all CRUD operations with Pydantic models",
                "completed": False,
                "priority": "high",
                "status": "in_progress",
                "due_date": "2025-09-30T23:59:59",
                "tags": ["work", "programming", "fastapi"],
                "created_at": "2025-09-24T10:00:00",
                "updated_at": "2025-09-24T12:00:00",
            }
        },
    )


class TodoList(BaseModel):
    """Pydantic model for Todo list response with metadata"""
    todos: List[TodoResponse] = Field(..., description="List of todo items")
    total: int = Field(..., ge=0, description="Total number of todos")
    page: int = Field(..., ge=1, description="Current page number")
    size: int = Field(..., ge=0, description="Number of items in current page")
    total_pages: int = Field(..., ge=0, description="Total number of pages")

    @model_validator(mode="after")
    def validate_pagination(self):
        """Validate pagination data consistency"""
        if self.size > self.total:
            raise ValueError("Page size cannot be greater than total items")
        return self


class TodoStats(BaseModel):
    """Pydantic model for Todo statistics"""

    total_todos: int = Field(ge=0)
    completed_todos: int = Field(ge=0)
    pending_todos: int = Field(ge=0)
    overdue_todos: int = Field(ge=0)
    completion_rate: float = Field(
        ge=0.0, le=1.0, description="Completion rate as percentage"
    )

    @model_validator(mode="after")
    def validate_stats(self):
        """Validate statistics consistency"""
        if self.completed_todos + self.pending_todos != self.total_todos:
            raise ValueError("Completed and pending todos must sum to total todos")
        return self


class TodoFilter(BaseModel):
    """Pydantic model for filtering todos"""

    completed: Optional[bool] = None
    priority: Optional[TodoPriority] = None
    status: Optional[TodoStatus] = None
    tags: Optional[List[str]] = None
    due_before: Optional[datetime] = None
    due_after: Optional[datetime] = None
    search: Optional[str] = Field(
        None, max_length=100, description="Search in title and description"
    )

    @field_validator("search")
    @classmethod
    def validate_search(cls, v: Optional[str]) -> Optional[str]:
        """Validate search term"""
        if v is not None:
            v = v.strip()
            return v if v else None
        return v