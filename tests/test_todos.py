"""
Test cases for Todo API endpoints
"""

import pytest
from fastapi import status
from fastapi.testclient import TestClient


class TestTodoAPI:
    """Test class for Todo API endpoints"""

    def test_create_todo(self, client: TestClient):
        """Test creating a new todo"""
        todo_data = {
            "title": "Test Todo",
            "description": "This is a test todo",
            "completed": False
        }
        
        response = client.post("/api/v1/todos/", json=todo_data)
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["title"] == todo_data["title"]
        assert data["description"] == todo_data["description"]
        assert data["completed"] == todo_data["completed"]
        assert "id" in data
        assert "created_at" in data

    def test_get_todos(self, client: TestClient):
        """Test getting list of todos"""
        # First create a todo
        todo_data = {
            "title": "Test Todo",
            "description": "This is a test todo"
        }
        client.post("/api/v1/todos/", json=todo_data)
        
        # Get todos
        response = client.get("/api/v1/todos/")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "todos" in data
        assert "total" in data
        assert "page" in data
        assert "size" in data
        assert len(data["todos"]) == 1

    def test_get_todo_by_id(self, client: TestClient):
        """Test getting a specific todo by ID"""
        # Create a todo
        todo_data = {
            "title": "Test Todo",
            "description": "This is a test todo"
        }
        create_response = client.post("/api/v1/todos/", json=todo_data)
        created_todo = create_response.json()
        
        # Get the todo by ID
        response = client.get(f"/api/v1/todos/{created_todo['id']}")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == created_todo["id"]
        assert data["title"] == todo_data["title"]

    def test_get_nonexistent_todo(self, client: TestClient):
        """Test getting a nonexistent todo"""
        response = client.get("/api/v1/todos/999")
        
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_update_todo(self, client: TestClient):
        """Test updating a todo"""
        # Create a todo
        todo_data = {
            "title": "Test Todo",
            "description": "This is a test todo"
        }
        create_response = client.post("/api/v1/todos/", json=todo_data)
        created_todo = create_response.json()
        
        # Update the todo
        update_data = {
            "title": "Updated Todo",
            "completed": True
        }
        response = client.put(f"/api/v1/todos/{created_todo['id']}", json=update_data)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["title"] == update_data["title"]
        assert data["completed"] == update_data["completed"]
        assert data["description"] == todo_data["description"]  # Should remain unchanged

    def test_delete_todo(self, client: TestClient):
        """Test deleting a todo"""
        # Create a todo
        todo_data = {
            "title": "Test Todo",
            "description": "This is a test todo"
        }
        create_response = client.post("/api/v1/todos/", json=todo_data)
        created_todo = create_response.json()
        
        # Delete the todo
        response = client.delete(f"/api/v1/todos/{created_todo['id']}")
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
        
        # Verify it's deleted
        get_response = client.get(f"/api/v1/todos/{created_todo['id']}")
        assert get_response.status_code == status.HTTP_404_NOT_FOUND

    def test_complete_todo(self, client: TestClient):
        """Test marking a todo as completed"""
        # Create a todo
        todo_data = {
            "title": "Test Todo",
            "description": "This is a test todo",
            "completed": False
        }
        create_response = client.post("/api/v1/todos/", json=todo_data)
        created_todo = create_response.json()
        
        # Complete the todo
        response = client.patch(f"/api/v1/todos/{created_todo['id']}/complete")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["completed"] == True

    def test_uncomplete_todo(self, client: TestClient):
        """Test marking a completed todo as not completed"""
        # Create a completed todo
        todo_data = {
            "title": "Test Todo",
            "description": "This is a test todo",
            "completed": True
        }
        create_response = client.post("/api/v1/todos/", json=todo_data)
        created_todo = create_response.json()
        
        # Uncomplete the todo
        response = client.patch(f"/api/v1/todos/{created_todo['id']}/uncomplete")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["completed"] == False

    def test_get_todos_with_filter(self, client: TestClient):
        """Test getting todos with completed filter"""
        # Create completed and uncompleted todos
        client.post("/api/v1/todos/", json={"title": "Completed Todo", "completed": True})
        client.post("/api/v1/todos/", json={"title": "Incomplete Todo", "completed": False})
        
        # Get only completed todos
        response = client.get("/api/v1/todos/?completed=true")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total"] == 1
        assert data["todos"][0]["completed"] == True
        
        # Get only incomplete todos
        response = client.get("/api/v1/todos/?completed=false")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total"] == 1
        assert data["todos"][0]["completed"] == False