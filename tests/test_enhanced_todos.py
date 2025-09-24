"""
Enhanced test cases for Pydantic-powered Todo API endpoints
"""

import pytest
from datetime import datetime, timedelta
from fastapi import status
from fastapi.testclient import TestClient

from fastapi_todo_app.schemas.todo import TodoPriority, TodoStatus


class TestEnhancedTodoAPI:
    """Test class for enhanced Todo API with Pydantic models"""

    def test_create_todo_with_pydantic_validation(self, client: TestClient):
        """Test creating a new todo with Pydantic validation"""
        todo_data = {
            "title": "Test Todo with Pydantic",
            "description": "This is a test todo with enhanced validation",
            "completed": False,
            "priority": "high",
            "status": "pending",
            "due_date": (datetime.now() + timedelta(days=7)).isoformat(),
            "tags": ["test", "pydantic", "fastapi"]
        }
        
        response = client.post("/api/v1/todos/", json=todo_data)
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["title"] == todo_data["title"]
        assert data["description"] == todo_data["description"]
        assert data["priority"] == todo_data["priority"]
        assert data["status"] == todo_data["status"]
        assert data["tags"] == todo_data["tags"]
        assert "id" in data
        assert "created_at" in data

    def test_create_todo_validation_errors(self, client: TestClient):
        """Test Pydantic validation errors"""
        # Test empty title
        todo_data = {
            "title": "",
            "description": "This should fail"
        }
        
        response = client.post("/api/v1/todos/", json=todo_data)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        
        # Test title too long
        todo_data = {
            "title": "x" * 201,  # Exceeds 200 character limit
            "description": "This should also fail"
        }
        
        response = client.post("/api/v1/todos/", json=todo_data)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_get_todos_with_enhanced_filtering(self, client: TestClient):
        """Test getting todos with enhanced filtering"""
        # Create test todos with different properties
        todos = [
            {
                "title": "High Priority Todo",
                "priority": "high",
                "status": "pending",
                "tags": ["urgent", "work"]
            },
            {
                "title": "Completed Todo",
                "priority": "medium",
                "status": "completed",
                "completed": True,
                "tags": ["done", "work"]
            },
            {
                "title": "Low Priority Todo",
                "priority": "low",
                "status": "in_progress",
                "tags": ["personal"]
            }
        ]
        
        # Create all todos
        for todo in todos:
            client.post("/api/v1/todos/", json=todo)
        
        # Test filtering by priority
        response = client.get("/api/v1/todos/?priority=high")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["todos"]) == 1
        assert data["todos"][0]["priority"] == "high"
        
        # Test filtering by status
        response = client.get("/api/v1/todos/?status=completed")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["todos"]) == 1
        assert data["todos"][0]["status"] == "completed"

    def test_todo_stats_endpoint(self, client: TestClient):
        """Test the todo statistics endpoint"""
        # Create some test todos
        client.post("/api/v1/todos/", json={"title": "Todo 1", "completed": False})
        client.post("/api/v1/todos/", json={"title": "Todo 2", "completed": True})
        
        response = client.get("/api/v1/todos/stats")
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert "total_todos" in data
        assert "completed_todos" in data
        assert "pending_todos" in data
        assert "completion_rate" in data
        assert data["total_todos"] >= 2

    def test_bulk_operations(self, client: TestClient):
        """Test bulk operations"""
        # Create multiple todos
        todos = [
            {"title": "Bulk Todo 1", "priority": "low"},
            {"title": "Bulk Todo 2", "priority": "medium"},
            {"title": "Bulk Todo 3", "priority": "high"}
        ]
        
        response = client.post("/api/v1/todos/bulk", json=todos)
        assert response.status_code == status.HTTP_201_CREATED
        
        data = response.json()
        assert len(data) == 3
        
        # Get the created todo IDs
        todo_ids = [todo["id"] for todo in data]
        
        # Test bulk status update
        bulk_update_data = {
            "todo_ids": todo_ids,
            "status": "completed"
        }
        
        response = client.patch("/api/v1/todos/bulk-status", json=bulk_update_data)
        assert response.status_code == status.HTTP_200_OK
        
        updated_todos = response.json()
        assert len(updated_todos) == 3
        for todo in updated_todos:
            assert todo["status"] == "completed"

    def test_advanced_search(self, client: TestClient):
        """Test advanced search functionality"""
        # Create todos with searchable content
        client.post("/api/v1/todos/", json={
            "title": "Python FastAPI Development",
            "description": "Working on FastAPI project with Pydantic",
            "tags": ["python", "development"]
        })
        
        # Test search functionality
        search_filters = {
            "search": "FastAPI",
            "tags": ["python"]
        }
        
        response = client.post("/api/v1/todos/search", json=search_filters)
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert len(data["todos"]) >= 1

    def test_priority_filtering(self, client: TestClient):
        """Test filtering todos by priority"""
        # Create todos with different priorities
        client.post("/api/v1/todos/", json={"title": "Urgent Task", "priority": "urgent"})
        
        response = client.get("/api/v1/todos/priority/urgent")
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert len(data) >= 1
        for todo in data:
            assert todo["priority"] == "urgent"

    def test_status_filtering(self, client: TestClient):
        """Test filtering todos by status"""
        # Create a todo with specific status
        client.post("/api/v1/todos/", json={"title": "In Progress Task", "status": "in_progress"})
        
        response = client.get("/api/v1/todos/status/in_progress")
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert len(data) >= 1
        for todo in data:
            assert todo["status"] == "in_progress"

    def test_overdue_todos(self, client: TestClient):
        """Test getting overdue todos"""
        # Create an overdue todo
        past_date = (datetime.now() - timedelta(days=1)).isoformat()
        client.post("/api/v1/todos/", json={
            "title": "Overdue Task",
            "due_date": past_date,
            "completed": False
        })
        
        response = client.get("/api/v1/todos/overdue")
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        # Should have at least the overdue todo we just created
        overdue_todos = [todo for todo in data if not todo["completed"]]
        assert len(overdue_todos) >= 1

    def test_pydantic_model_validation_in_updates(self, client: TestClient):
        """Test Pydantic validation during updates"""
        # Create a todo
        create_response = client.post("/api/v1/todos/", json={"title": "Update Test"})
        todo_id = create_response.json()["id"]
        
        # Test valid update
        update_data = {
            "title": "Updated Title",
            "priority": "high",
            "tags": ["updated", "test"]
        }
        
        response = client.put(f"/api/v1/todos/{todo_id}", json=update_data)
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert data["title"] == update_data["title"]
        assert data["priority"] == update_data["priority"]
        assert data["tags"] == update_data["tags"]

    def test_enhanced_todo_response_structure(self, client: TestClient):
        """Test the enhanced TodoResponse Pydantic model structure"""
        todo_data = {
            "title": "Complete Response Test",
            "description": "Testing complete response structure",
            "priority": "medium",
            "status": "pending",
            "tags": ["response", "test"]
        }
        
        response = client.post("/api/v1/todos/", json=todo_data)
        assert response.status_code == status.HTTP_201_CREATED
        
        data = response.json()
        
        # Verify all expected fields are present
        expected_fields = [
            "id", "title", "description", "completed", "priority", 
            "status", "due_date", "tags", "created_at", "updated_at"
        ]
        
        for field in expected_fields:
            assert field in data
        
        # Verify data types and values
        assert isinstance(data["id"], int)
        assert isinstance(data["title"], str)
        assert isinstance(data["completed"], bool)
        assert isinstance(data["tags"], list)
        assert data["priority"] in ["low", "medium", "high", "urgent"]
        assert data["status"] in ["pending", "in_progress", "completed", "cancelled"]