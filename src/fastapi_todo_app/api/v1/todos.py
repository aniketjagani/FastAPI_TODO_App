"""
Enhanced Todo API endpoints with comprehensive Pydantic model integration
"""

from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, status, Body
from sqlalchemy.orm import Session
import math

from ...db.database import get_db
from ...schemas.todo import (
    TodoCreate,
    TodoUpdate,
    TodoResponse,
    TodoList,
    TodoFilter,
    TodoStats,
    TodoStatus,
    TodoPriority,
)
from ...services.todo_service import TodoService

router = APIRouter()


@router.get("/", response_model=TodoList)
async def get_todos(
    skip: int = Query(0, ge=0, description="Number of todos to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of todos to return"),
    completed: Optional[bool] = Query(None, description="Filter by completed status"),
    priority: Optional[TodoPriority] = Query(None, description="Filter by priority"),
    status: Optional[TodoStatus] = Query(None, description="Filter by status"),
    search: Optional[str] = Query(
        None, max_length=100, description="Search in title and description"
    ),
    tags: Optional[str] = Query(
        None, description="Comma-separated list of tags to filter by"
    ),
    db: Session = Depends(get_db),
):
    """Get all todos with enhanced filtering and pagination"""

    # Create filter object from query parameters
    filters = TodoFilter(
        completed=completed,
        priority=priority,
        status=status,
        search=search,
        tags=tags.split(",") if tags else None,
    )

    todos = TodoService.get_todos(db, skip=skip, limit=limit, filters=filters)
    total = TodoService.get_todos_count(db, filters=filters)

    # Calculate total pages
    total_pages = math.ceil(total / limit) if total > 0 else 0

    return TodoList(
        todos=todos,
        total=total,
        page=skip // limit + 1,
        size=len(todos),
        total_pages=total_pages,
    )


@router.get("/stats", response_model=TodoStats)
async def get_todo_stats(db: Session = Depends(get_db)):
    """Get comprehensive todo statistics"""
    return TodoService.get_todo_stats(db)


@router.get("/priority/{priority}", response_model=List[TodoResponse])
async def get_todos_by_priority(priority: TodoPriority, db: Session = Depends(get_db)):
    """Get todos filtered by priority level"""
    todos = TodoService.get_todos_by_priority(db, priority)
    return todos


@router.get("/status/{status_filter}", response_model=List[TodoResponse])
async def get_todos_by_status(status_filter: TodoStatus, db: Session = Depends(get_db)):
    """Get todos filtered by status"""
    todos = TodoService.get_todos_by_status(db, status_filter)
    return todos


@router.get("/overdue", response_model=List[TodoResponse])
async def get_overdue_todos(db: Session = Depends(get_db)):
    """Get all overdue todos"""
    todos = TodoService.get_overdue_todos(db)
    return todos


@router.get("/{todo_id}", response_model=TodoResponse)
async def get_todo(todo_id: int, db: Session = Depends(get_db)):
    """Get a specific todo by ID"""
    todo = TodoService.get_todo_by_id(db, todo_id)
    
    if not todo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Todo not found"
        )
    
    return todo


@router.post("/", response_model=TodoResponse, status_code=status.HTTP_201_CREATED)
async def create_todo(todo: TodoCreate, db: Session = Depends(get_db)):
    """Create a new todo with enhanced validation"""
    return TodoService.create_todo(db, todo)


@router.post(
    "/bulk", response_model=List[TodoResponse], status_code=status.HTTP_201_CREATED
)
async def create_multiple_todos(todos: List[TodoCreate], db: Session = Depends(get_db)):
    """Create multiple todos at once"""
    created_todos = []
    for todo in todos:
        created_todo = TodoService.create_todo(db, todo)
        created_todos.append(created_todo)
    return created_todos


@router.put("/{todo_id}", response_model=TodoResponse)
async def update_todo(
    todo_id: int,
    todo_update: TodoUpdate,
    db: Session = Depends(get_db)
):
    """Update an existing todo with enhanced validation"""
    return TodoService.update_todo(db, todo_id, todo_update)


@router.patch("/bulk-status", response_model=List[TodoResponse])
async def bulk_update_status(
    todo_ids: List[int] = Body(..., description="List of todo IDs to update"),
    status: TodoStatus = Body(..., description="New status for all todos"),
    db: Session = Depends(get_db),
):
    """Bulk update status for multiple todos"""
    return TodoService.bulk_update_status(db, todo_ids, status)


@router.delete("/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_todo(todo_id: int, db: Session = Depends(get_db)):
    """Delete a todo"""
    TodoService.delete_todo(db, todo_id)


@router.patch("/{todo_id}/complete", response_model=TodoResponse)
async def complete_todo(todo_id: int, db: Session = Depends(get_db)):
    """Mark a todo as completed"""
    return TodoService.mark_todo_completed(db, todo_id)


@router.patch("/{todo_id}/uncomplete", response_model=TodoResponse)
async def uncomplete_todo(todo_id: int, db: Session = Depends(get_db)):
    """Mark a todo as not completed"""
    return TodoService.mark_todo_uncompleted(db, todo_id)


@router.post("/search", response_model=TodoList)
async def search_todos(
    filters: TodoFilter,
    skip: int = Query(0, ge=0, description="Number of todos to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of todos to return"),
    db: Session = Depends(get_db),
):
    """Advanced search for todos using comprehensive filter model"""
    todos = TodoService.get_todos(db, skip=skip, limit=limit, filters=filters)
    total = TodoService.get_todos_count(db, filters=filters)

    # Calculate total pages
    total_pages = math.ceil(total / limit) if total > 0 else 0

    return TodoList(
        todos=todos,
        total=total,
        page=skip // limit + 1,
        size=len(todos),
        total_pages=total_pages,
    )
