"""
Comprehensive Testing Framework for FastAPI TODO Application
"""

import pytest
import asyncio
import json
from typing import Dict, Any, Generator
from httpx import AsyncClient
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import tempfile
import os

# Import application components
from src.fastapi_todo_app.main import app
from src.fastapi_todo_app.shared.core.config import settings
from src.fastapi_todo_app.domains.todos.db.database import Base as TodoBase, get_db as get_todo_db
from src.fastapi_todo_app.domains.employees.db.database import Base as EmployeeBase, get_db as get_employee_db


class TestDatabaseManager:
    """Manages test database lifecycle"""
    
    def __init__(self):
        self.todo_engine = None
        self.employee_engine = None
        self.todo_session = None
        self.employee_session = None
    
    def setup_test_databases(self):
        """Setup test databases"""
        # Create temporary database files
        self.todo_db_file = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.employee_db_file = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        
        # Create engines
        self.todo_engine = create_engine(
            f"sqlite:///{self.todo_db_file.name}",
            connect_args={"check_same_thread": False}
        )
        self.employee_engine = create_engine(
            f"sqlite:///{self.employee_db_file.name}",
            connect_args={"check_same_thread": False}
        )
        
        # Create tables
        TodoBase.metadata.create_all(bind=self.todo_engine)
        EmployeeBase.metadata.create_all(bind=self.employee_engine)
        
        # Create sessions
        TodoSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.todo_engine)
        EmployeeSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.employee_engine)
        
        self.todo_session = TodoSessionLocal()
        self.employee_session = EmployeeSessionLocal()
    
    def get_test_todo_db(self):
        """Get test todo database session"""
        try:
            yield self.todo_session
        finally:
            self.todo_session.close()
    
    def get_test_employee_db(self):
        """Get test employee database session"""
        try:
            yield self.employee_session
        finally:
            self.employee_session.close()
    
    def cleanup(self):
        """Clean up test databases"""
        if self.todo_session:
            self.todo_session.close()
        if self.employee_session:
            self.employee_session.close()
        
        # Remove temporary files
        if hasattr(self, 'todo_db_file'):
            os.unlink(self.todo_db_file.name)
        if hasattr(self, 'employee_db_file'):
            os.unlink(self.employee_db_file.name)


@pytest.fixture(scope="session")
def test_db_manager():
    """Test database manager fixture"""
    manager = TestDatabaseManager()
    manager.setup_test_databases()
    yield manager
    manager.cleanup()


@pytest.fixture
def test_app(test_db_manager):
    """Test application with database overrides"""
    # Override database dependencies
    app.dependency_overrides[get_todo_db] = test_db_manager.get_test_todo_db
    app.dependency_overrides[get_employee_db] = test_db_manager.get_test_employee_db
    
    yield app
    
    # Clear overrides
    app.dependency_overrides.clear()


@pytest.fixture
def client(test_app):
    """Test client fixture"""
    return TestClient(test_app)


@pytest.fixture
async def async_client(test_app):
    """Async test client fixture"""
    async with AsyncClient(app=test_app, base_url="http://testserver") as ac:
        yield ac


# Test Data Fixtures
@pytest.fixture
def sample_todo_data():
    """Sample TODO data for testing"""
    return {
        "title": "Test TODO",
        "description": "This is a test TODO item",
        "priority": "high",
        "due_date": "2025-12-31T23:59:59",
        "tags": ["testing", "important"]
    }


@pytest.fixture
def sample_employee_data():
    """Sample employee data for testing"""
    return {
        "name": "John Doe",
        "email": "john.doe@example.com",
        "department": "Engineering",
        "position": "Software Developer",
        "salary": 75000.00
    }


# Performance Testing
class PerformanceTest:
    """Performance testing utilities"""
    
    @staticmethod
    async def measure_response_time(client: AsyncClient, method: str, url: str, **kwargs) -> float:
        """Measure response time for an API call"""
        import time
        start_time = time.time()
        
        if method.upper() == 'GET':
            response = await client.get(url, **kwargs)
        elif method.upper() == 'POST':
            response = await client.post(url, **kwargs)
        elif method.upper() == 'PUT':
            response = await client.put(url, **kwargs)
        elif method.upper() == 'DELETE':
            response = await client.delete(url, **kwargs)
        
        end_time = time.time()
        response_time = end_time - start_time
        
        return response_time, response
    
    @staticmethod
    async def load_test(client: AsyncClient, method: str, url: str, concurrent_requests: int = 10, **kwargs):
        """Perform load testing"""
        import asyncio
        
        async def single_request():
            return await PerformanceTest.measure_response_time(client, method, url, **kwargs)
        
        # Run concurrent requests
        tasks = [single_request() for _ in range(concurrent_requests)]
        results = await asyncio.gather(*tasks)
        
        response_times = [result[0] for result in results]
        responses = [result[1] for result in results]
        
        return {
            'total_requests': len(results),
            'avg_response_time': sum(response_times) / len(response_times),
            'min_response_time': min(response_times),
            'max_response_time': max(response_times),
            'success_count': sum(1 for r in responses if 200 <= r.status_code < 300),
            'error_count': sum(1 for r in responses if r.status_code >= 400)
        }


# Security Testing
class SecurityTest:
    """Security testing utilities"""
    
    @staticmethod
    def test_sql_injection_payloads():
        """Common SQL injection payloads"""
        return [
            "' OR '1'='1",
            "'; DROP TABLE todos; --",
            "' UNION SELECT * FROM users --",
            "1' OR 1=1 --",
            "admin'/*",
            "' OR 'x'='x",
        ]
    
    @staticmethod
    def test_xss_payloads():
        """Common XSS payloads"""
        return [
            "<script>alert('XSS')</script>",
            "javascript:alert('XSS')",
            "<img src=x onerror=alert('XSS')>",
            "<svg onload=alert('XSS')>",
            "';alert('XSS');//",
        ]
    
    @staticmethod
    async def test_unauthorized_access(client: AsyncClient, protected_endpoints: list):
        """Test unauthorized access to protected endpoints"""
        results = {}
        
        for endpoint in protected_endpoints:
            response = await client.get(endpoint)
            results[endpoint] = {
                'status_code': response.status_code,
                'should_be_401_or_403': response.status_code in [401, 403]
            }
        
        return results


# Data Validation Testing
class ValidationTest:
    """Data validation testing utilities"""
    
    @staticmethod
    def generate_invalid_todo_data():
        """Generate invalid TODO data for validation testing"""
        return [
            {},  # Empty data
            {"title": ""},  # Empty title
            {"title": "A" * 1000},  # Title too long
            {"title": "Test", "priority": "invalid"},  # Invalid priority
            {"title": "Test", "due_date": "invalid-date"},  # Invalid date format
            {"title": "Test", "tags": "not-a-list"},  # Invalid tags format
        ]
    
    @staticmethod
    def generate_invalid_employee_data():
        """Generate invalid employee data for validation testing"""
        return [
            {},  # Empty data
            {"name": ""},  # Empty name
            {"name": "Test", "email": "invalid-email"},  # Invalid email
            {"name": "Test", "email": "test@test.com", "salary": -1000},  # Negative salary
            {"name": "A" * 1000, "email": "test@test.com"},  # Name too long
        ]


# Integration Test Base Class
class IntegrationTestBase:
    """Base class for integration tests"""
    
    async def setup_test_data(self, client: AsyncClient) -> Dict[str, Any]:
        """Setup test data for integration tests"""
        test_data = {}
        
        # Create test TODO
        todo_data = {
            "title": "Integration Test TODO",
            "description": "TODO for integration testing",
            "priority": "medium"
        }
        
        todo_response = await client.post("/api/v1/todos", json=todo_data)
        if todo_response.status_code == 201:
            test_data['todo'] = todo_response.json()
        
        # Create test Employee
        employee_data = {
            "name": "Integration Test Employee",
            "email": "integration@test.com",
            "department": "Testing",
            "position": "Test Engineer"
        }
        
        employee_response = await client.post("/api/v1/employees", json=employee_data)
        if employee_response.status_code == 201:
            test_data['employee'] = employee_response.json()
        
        return test_data
    
    async def cleanup_test_data(self, client: AsyncClient, test_data: Dict[str, Any]):
        """Clean up test data after integration tests"""
        # Delete test TODO
        if 'todo' in test_data:
            todo_id = test_data['todo']['id']
            await client.delete(f"/api/v1/todos/{todo_id}")
        
        # Delete test Employee
        if 'employee' in test_data:
            employee_id = test_data['employee']['id']
            await client.delete(f"/api/v1/employees/{employee_id}")


# Custom Pytest Markers
pytest.mark.unit = pytest.mark.unit
pytest.mark.integration = pytest.mark.integration
pytest.mark.performance = pytest.mark.performance
pytest.mark.security = pytest.mark.security
pytest.mark.slow = pytest.mark.slow


# Export test utilities
__all__ = [
    'TestDatabaseManager',
    'PerformanceTest',
    'SecurityTest',
    'ValidationTest',
    'IntegrationTestBase',
]