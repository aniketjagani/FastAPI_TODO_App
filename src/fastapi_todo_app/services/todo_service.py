"""
Todo service layer for business logic
"""

from typing import List, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from ..models.todo import Todo
from ..schemas.todo import TodoCreate, TodoUpdate


class TodoService:
    """Service class for Todo operations"""
    
    @staticmethod
    def get_todo_by_id(db: Session, todo_id: int) -> Optional[Todo]:
        """Get a todo by its ID"""
        return db.query(Todo).filter(Todo.id == todo_id).first()
    
    @staticmethod
    def get_todos(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        completed: Optional[bool] = None
    ) -> List[Todo]:
        """Get todos with pagination and optional filter by completed status"""
        query = db.query(Todo)
        
        if completed is not None:
            query = query.filter(Todo.completed == completed)
        
        return query.offset(skip).limit(limit).all()
    
    @staticmethod
    def get_todos_count(db: Session, completed: Optional[bool] = None) -> int:
        """Get total count of todos"""
        query = db.query(Todo)
        
        if completed is not None:
            query = query.filter(Todo.completed == completed)
        
        return query.count()
    
    @staticmethod
    def create_todo(db: Session, todo: TodoCreate) -> Todo:
        """Create a new todo"""
        db_todo = Todo(**todo.model_dump())
        db.add(db_todo)
        db.commit()
        db.refresh(db_todo)
        return db_todo
    
    @staticmethod
    def update_todo(db: Session, todo_id: int, todo_update: TodoUpdate) -> Todo:
        """Update an existing todo"""
        db_todo = TodoService.get_todo_by_id(db, todo_id)
        
        if not db_todo:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Todo not found"
            )
        
        update_data = todo_update.model_dump(exclude_unset=True)
        
        for field, value in update_data.items():
            setattr(db_todo, field, value)
        
        db.commit()
        db.refresh(db_todo)
        return db_todo
    
    @staticmethod
    def delete_todo(db: Session, todo_id: int) -> bool:
        """Delete a todo by its ID"""
        db_todo = TodoService.get_todo_by_id(db, todo_id)
        
        if not db_todo:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Todo not found"
            )
        
        db.delete(db_todo)
        db.commit()
        return True
    
    @staticmethod
    def mark_todo_completed(db: Session, todo_id: int) -> Todo:
        """Mark a todo as completed"""
        return TodoService.update_todo(
            db, todo_id, TodoUpdate(completed=True)
        )
    
    @staticmethod
    def mark_todo_uncompleted(db: Session, todo_id: int) -> Todo:
        """Mark a todo as not completed"""
        return TodoService.update_todo(
            db, todo_id, TodoUpdate(completed=False)
        )