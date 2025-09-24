# FastAPI TODO App 🚀

A modern, high-performance TODO application built with FastAPI, SQLAlchemy, and UV package manager.

## Features ✨

- **Fast & Modern**: Built with FastAPI for high performance and automatic API documentation
- **Type Safety**: Full type hints and Pydantic models for request/response validation
- **Database**: SQLAlchemy ORM with support for SQLite, PostgreSQL, and MySQL
- **Modern Package Management**: Uses UV instead of pip for faster dependency resolution
- **Testing**: Comprehensive test suite with pytest and async support
- **Code Quality**: Pre-configured with Black, isort, flake8, and mypy
- **API Documentation**: Automatic OpenAPI/Swagger documentation
- **CORS Support**: Configurable CORS for frontend integration

## API Endpoints 📚

### Todos
- `GET /api/v1/todos/` - List todos with pagination and filtering
- `POST /api/v1/todos/` - Create a new todo
- `GET /api/v1/todos/{id}` - Get a specific todo
- `PUT /api/v1/todos/{id}` - Update a todo
- `DELETE /api/v1/todos/{id}` - Delete a todo
- `PATCH /api/v1/todos/{id}/complete` - Mark todo as completed
- `PATCH /api/v1/todos/{id}/uncomplete` - Mark todo as incomplete

### Health
- `GET /` - Root endpoint
- `GET /health` - Health check endpoint

## Quick Start 🏃‍♂️

### Prerequisites

- Python 3.13+
- UV package manager

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/aniketjagani/FastAPI_TODO_App.git
   cd FastAPI_TODO_App
   ```

2. **Install dependencies with UV**
   ```bash
   uv sync
   ```

3. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env file with your configuration
   ```

4. **Run the application**
   ```bash
   uv run fastapi-todo-app
   ```

   Or alternatively:
   ```bash
   uv run uvicorn fastapi_todo_app.main:app --reload
   ```

5. **Access the application**
   - API: http://localhost:8000
   - Interactive API docs: http://localhost:8000/docs
   - Alternative docs: http://localhost:8000/redoc

## Development 🛠️

### Project Structure

```
FastAPI_TODO_App/
├── src/
│   └── fastapi_todo_app/
│       ├── __init__.py          # Package initialization
│       ├── main.py              # FastAPI application entry point
│       ├── api/                 # API layer
│       │   └── v1/
│       │       ├── api.py       # API router aggregation
│       │       └── todos.py     # Todo endpoints
│       ├── core/                # Core application configuration
│       │   └── config.py        # Settings and configuration
│       ├── db/                  # Database layer
│       │   └── database.py      # Database connection and session
│       ├── models/              # SQLAlchemy models
│       │   └── todo.py          # Todo database model
│       ├── schemas/             # Pydantic schemas
│       │   └── todo.py          # Todo request/response schemas
│       └── services/            # Business logic layer
│           └── todo_service.py  # Todo business logic
├── tests/                       # Test suite
│   ├── conftest.py             # Test configuration
│   └── test_todos.py           # Todo API tests
├── pyproject.toml              # Project configuration and dependencies
└── .env.example                # Environment variables template
```

### Running Tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=src --cov-report=html

# Run specific test file
uv run pytest tests/test_todos.py
```

### Code Quality

```bash
# Format code with Black
uv run black src tests

# Sort imports with isort
uv run isort src tests

# Lint with flake8
uv run flake8 src tests

# Type checking with mypy
uv run mypy src
```

### Adding Dependencies

```bash
# Add production dependency
uv add package-name

# Add development dependency
uv add --dev package-name
```

## Configuration ⚙️

The application can be configured using environment variables or a `.env` file:

| Variable | Description | Default |
|----------|-------------|---------|
| `PROJECT_NAME` | Application name | FastAPI TODO App |
| `VERSION` | Application version | 1.0.0 |
| `ENVIRONMENT` | Environment (development/production) | development |
| `DEBUG` | Enable debug mode | true |
| `SECRET_KEY` | Secret key for security | your-secret-key-change-this |
| `DATABASE_URL` | Database connection URL | sqlite:///./todo_app.db |
| `BACKEND_CORS_ORIGINS` | Allowed CORS origins | localhost origins |

## Database Support 💾

The application supports multiple databases:

### SQLite (Default)
```
DATABASE_URL=sqlite:///./todo_app.db
```

### PostgreSQL
```
DATABASE_URL=postgresql://user:password@localhost/dbname
```

### MySQL
```
DATABASE_URL=mysql://user:password@localhost/dbname
```

## Docker Support 🐳

Create a `Dockerfile` for containerization:

```dockerfile
FROM python:3.13-slim

WORKDIR /app

# Install UV
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Copy project files
COPY pyproject.toml ./
COPY src ./src

# Install dependencies
RUN uv sync --frozen

# Run the application
CMD ["uv", "run", "fastapi-todo-app"]
```

## API Documentation 📖

Once the application is running, you can access:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/api/v1/openapi.json

## Contributing 🤝

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes
4. Run tests: `uv run pytest`
5. Format code: `uv run black src tests`
6. Commit changes: `git commit -am 'Add feature'`
7. Push to branch: `git push origin feature-name`
8. Submit a pull request

## License 📄

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Technologies Used 🔧

- **[FastAPI](https://fastapi.tiangolo.com/)** - Modern, fast web framework for Python
- **[SQLAlchemy](https://www.sqlalchemy.org/)** - SQL toolkit and ORM
- **[Pydantic](https://pydantic-docs.helpmanual.io/)** - Data validation using Python type annotations
- **[UV](https://github.com/astral-sh/uv)** - Fast Python package manager
- **[Uvicorn](https://www.uvicorn.org/)** - ASGI server for production
- **[Pytest](https://pytest.org/)** - Testing framework
- **[Black](https://black.readthedocs.io/)** - Code formatter
- **[isort](https://isort.readthedocs.io/)** - Import sorter
- **[MyPy](https://mypy.readthedocs.io/)** - Static type checker
