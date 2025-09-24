"""
Database models
"""

from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text
from sqlalchemy.sql import func

from ..db.database import Base


class Todo(Base):
    """
    Todo model for storing todo items
    """
    __tablename__ = "todos"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False, index=True)
    description = Column(Text, nullable=True)
    completed = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self) -> str:
        return f"<Todo(id={self.id}, title='{self.title}', completed={self.completed})>"