"""
SQLAlchemy database models with enhanced fields to support Pydantic models
"""

from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text, JSON
from sqlalchemy.sql import func

from ..db.database import Base


class Todo(Base):
    """
    Enhanced Todo SQLAlchemy model with additional fields for comprehensive todo management
    """
    __tablename__ = "todos"

    # Primary fields
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False, index=True)
    description = Column(Text, nullable=True)
    completed = Column(Boolean, default=False, nullable=False, index=True)

    # Enhanced fields
    priority = Column(String(20), default="medium", nullable=False, index=True)
    status = Column(String(20), default="pending", nullable=False, index=True)
    due_date = Column(DateTime(timezone=True), nullable=True, index=True)
    tags = Column(JSON, default=list, nullable=False)  # Store tags as JSON array

    # Timestamps
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

    def __repr__(self) -> str:
        return f"<Todo(id={self.id}, title='{self.title}', status='{self.status}', completed={self.completed})>"

    def to_dict(self) -> dict:
        """Convert SQLAlchemy model to dictionary for easy Pydantic conversion"""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "completed": self.completed,
            "priority": self.priority,
            "status": self.status,
            "due_date": self.due_date,
            "tags": self.tags or [],
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_pydantic(cls, pydantic_model) -> "Todo":
        """Create SQLAlchemy model from Pydantic model"""
        # Extract only the fields that exist in the SQLAlchemy model
        model_data = {}

        # Handle all the fields
        for field in [
            "title",
            "description",
            "completed",
            "priority",
            "status",
            "due_date",
            "tags",
        ]:
            if hasattr(pydantic_model, field):
                value = getattr(pydantic_model, field)
                if field == "priority" and hasattr(value, "value"):
                    # Handle enum values
                    model_data[field] = value.value
                elif field == "status" and hasattr(value, "value"):
                    # Handle enum values
                    model_data[field] = value.value
                else:
                    model_data[field] = value

        return cls(**model_data)
