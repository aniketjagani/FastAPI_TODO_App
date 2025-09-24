"""
Simple test to verify the FastAPI application is working
"""
import requests

def test_api():
    base_url = "http://localhost:8000"
    
    try:
        # Test root endpoint
        response = requests.get(f"{base_url}/")
        print(f"Root endpoint status: {response.status_code}")
        print(f"Root endpoint response: {response.json()}")
        
        # Test health endpoint
        response = requests.get(f"{base_url}/health")
        print(f"Health endpoint status: {response.status_code}")
        print(f"Health endpoint response: {response.json()}")
        
        # Test creating a todo
        todo_data = {
            "title": "Test Todo",
            "description": "This is a test todo",
            "completed": False
        }
        response = requests.post(f"{base_url}/api/v1/todos/", json=todo_data)
        print(f"Create todo status: {response.status_code}")
        if response.status_code == 201:
            created_todo = response.json()
            print(f"Created todo: {created_todo}")
            
            # Test getting todos
            response = requests.get(f"{base_url}/api/v1/todos/")
            print(f"Get todos status: {response.status_code}")
            print(f"Todos list: {response.json()}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Server is not running. Please start the server with:")
        print("   C:\\Users\\anike\\.local\\bin\\uv.exe run fastapi-todo-app")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_api()