"""
Enhanced Todo service layer with comprehensive business logic using Pydantic models
"""

from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from fastapi import HTTPException, status

from ..models.todo import Todo
from ..schemas.todo import (
    TodoCreate,
    TodoUpdate,
    TodoFilter,
    TodoStats,
    TodoStatus,
    TodoPriority,
)


class TodoService:
    """Enhanced service class for Todo operations with Pydantic integration"""

    @staticmethod
    def get_todo_by_id(db: Session, todo_id: int) -> Optional[Todo]:
        """Get a todo by its ID"""
        return db.query(Todo).filter(Todo.id == todo_id).first()

    @staticmethod
    def get_todos(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[TodoFilter] = None,
    ) -> List[Todo]:
        """Get todos with enhanced filtering using Pydantic filter model"""
        query = db.query(Todo)

        if filters:
            # Apply filters based on Pydantic model
            if filters.completed is not None:
                query = query.filter(Todo.completed == filters.completed)

            if filters.priority is not None:
                query = query.filter(Todo.priority == filters.priority.value)

            if filters.status is not None:
                query = query.filter(Todo.status == filters.status.value)

            if filters.tags:
                # Filter by tags (JSON contains any of the specified tags)
                tag_conditions = []
                for tag in filters.tags:
                    tag_conditions.append(
                        func.json_extract(Todo.tags, "$[*]").like(f"%{tag}%")
                    )
                query = query.filter(or_(*tag_conditions))

            if filters.due_before:
                query = query.filter(Todo.due_date <= filters.due_before)

            if filters.due_after:
                query = query.filter(Todo.due_date >= filters.due_after)

            if filters.search:
                search_term = f"%{filters.search}%"
                query = query.filter(
                    or_(
                        Todo.title.ilike(search_term),
                        Todo.description.ilike(search_term),
                    )
                )

        # Order by created_at descending by default
        query = query.order_by(Todo.created_at.desc())

        return query.offset(skip).limit(limit).all()

    @staticmethod
    def get_todos_count(db: Session, filters: Optional[TodoFilter] = None) -> int:
        """Get total count of todos with filtering"""
        query = db.query(Todo)

        if filters:
            # Apply the same filters as in get_todos
            if filters.completed is not None:
                query = query.filter(Todo.completed == filters.completed)

            if filters.priority is not None:
                query = query.filter(Todo.priority == filters.priority.value)

            if filters.status is not None:
                query = query.filter(Todo.status == filters.status.value)

            if filters.tags:
                tag_conditions = []
                for tag in filters.tags:
                    tag_conditions.append(
                        func.json_extract(Todo.tags, "$[*]").like(f"%{tag}%")
                    )
                query = query.filter(or_(*tag_conditions))

            if filters.due_before:
                query = query.filter(Todo.due_date <= filters.due_before)

            if filters.due_after:
                query = query.filter(Todo.due_date >= filters.due_after)

            if filters.search:
                search_term = f"%{filters.search}%"
                query = query.filter(
                    or_(
                        Todo.title.ilike(search_term),
                        Todo.description.ilike(search_term),
                    )
                )

        return query.count()

    @staticmethod
    def create_todo(db: Session, todo: TodoCreate) -> Todo:
        """Create a new todo using Pydantic model"""
        try:
            # Use the from_pydantic method to create SQLAlchemy model
            db_todo = Todo.from_pydantic(todo)
            db.add(db_todo)
            db.commit()
            db.refresh(db_todo)
            return db_todo
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Error creating todo: {str(e)}",
            )

    @staticmethod
    def update_todo(db: Session, todo_id: int, todo_update: TodoUpdate) -> Todo:
        """Update an existing todo using Pydantic model"""
        db_todo = TodoService.get_todo_by_id(db, todo_id)

        if not db_todo:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Todo not found"
            )

        try:
            update_data = todo_update.model_dump(exclude_unset=True)

            for field, value in update_data.items():
                if field in ["priority", "status"] and hasattr(value, "value"):
                    # Handle enum values
                    setattr(db_todo, field, value.value)
                else:
                    setattr(db_todo, field, value)

            db.commit()
            db.refresh(db_todo)
            return db_todo
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Error updating todo: {str(e)}",
            )

    @staticmethod
    def delete_todo(db: Session, todo_id: int) -> bool:
        """Delete a todo by its ID"""
        db_todo = TodoService.get_todo_by_id(db, todo_id)

        if not db_todo:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Todo not found"
            )

        try:
            db.delete(db_todo)
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error deleting todo: {str(e)}",
            )

    @staticmethod
    def mark_todo_completed(db: Session, todo_id: int) -> Todo:
        """Mark a todo as completed"""
        return TodoService.update_todo(
            db, todo_id, TodoUpdate(completed=True, status=TodoStatus.COMPLETED)
        )

    @staticmethod
    def mark_todo_uncompleted(db: Session, todo_id: int) -> Todo:
        """Mark a todo as not completed"""
        return TodoService.update_todo(
            db, todo_id, TodoUpdate(completed=False, status=TodoStatus.PENDING)
        )

    @staticmethod
    def get_todo_stats(db: Session) -> TodoStats:
        """Get comprehensive todo statistics"""
        total_todos = db.query(Todo).count()
        completed_todos = db.query(Todo).filter(Todo.completed == True).count()
        pending_todos = total_todos - completed_todos

        # Count overdue todos
        now = datetime.now()
        overdue_todos = (
            db.query(Todo)
            .filter(
                and_(
                    Todo.completed == False,
                    Todo.due_date < now,
                    Todo.due_date.is_not(None),
                )
            )
            .count()
        )

        completion_rate = completed_todos / total_todos if total_todos > 0 else 0.0

        return TodoStats(
            total_todos=total_todos,
            completed_todos=completed_todos,
            pending_todos=pending_todos,
            overdue_todos=overdue_todos,
            completion_rate=completion_rate,
        )

    @staticmethod
    def get_todos_by_priority(db: Session, priority: TodoPriority) -> List[Todo]:
        """Get todos filtered by priority"""
        return db.query(Todo).filter(Todo.priority == priority.value).all()

    @staticmethod
    def get_todos_by_status(db: Session, status: TodoStatus) -> List[Todo]:
        """Get todos filtered by status"""
        return db.query(Todo).filter(Todo.status == status.value).all()

    @staticmethod
    def get_overdue_todos(db: Session) -> List[Todo]:
        """Get all overdue todos"""
        now = datetime.now()
        return (
            db.query(Todo)
            .filter(
                and_(
                    Todo.completed == False,
                    Todo.due_date < now,
                    Todo.due_date.is_not(None),
                )
            )
            .all()
        )

    @staticmethod
    def bulk_update_status(
        db: Session, todo_ids: List[int], status: TodoStatus
    ) -> List[Todo]:
        """Bulk update status for multiple todos"""
        try:
            todos = db.query(Todo).filter(Todo.id.in_(todo_ids)).all()

            if not todos:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="No todos found with the provided IDs",
                )

            for todo in todos:
                todo.status = status.value
                if status == TodoStatus.COMPLETED:
                    todo.completed = True
                elif status in [TodoStatus.PENDING, TodoStatus.IN_PROGRESS]:
                    todo.completed = False

            db.commit()

            # Refresh all todos
            for todo in todos:
                db.refresh(todo)

            return todos
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Error bulk updating todos: {str(e)}",
            )
