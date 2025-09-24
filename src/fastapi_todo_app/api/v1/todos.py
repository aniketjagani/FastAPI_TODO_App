"""
Todo API endpoints
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from ...db.database import get_db
from ...schemas.todo import TodoCreate, TodoUpdate, TodoResponse, TodoList
from ...services.todo_service import TodoService

router = APIRouter()


@router.get("/", response_model=TodoList)
async def get_todos(
    skip: int = Query(0, ge=0, description="Number of todos to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of todos to return"),
    completed: Optional[bool] = Query(None, description="Filter by completed status"),
    db: Session = Depends(get_db)
):
    """Get all todos with pagination and optional filtering"""
    todos = TodoService.get_todos(db, skip=skip, limit=limit, completed=completed)
    total = TodoService.get_todos_count(db, completed=completed)
    
    return TodoList(
        todos=todos,
        total=total,
        page=skip // limit + 1,
        size=len(todos)
    )


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
    """Create a new todo"""
    return TodoService.create_todo(db, todo)


@router.put("/{todo_id}", response_model=TodoResponse)
async def update_todo(
    todo_id: int,
    todo_update: TodoUpdate,
    db: Session = Depends(get_db)
):
    """Update an existing todo"""
    return TodoService.update_todo(db, todo_id, todo_update)


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