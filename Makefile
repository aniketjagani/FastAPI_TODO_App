# FastAPI TODO App Makefile

.PHONY: help install dev test format lint clean run docker-build docker-run

help: ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install dependencies with uv
	uv sync

dev: ## Install development dependencies
	uv sync --all-extras

test: ## Run tests
	uv run pytest

test-cov: ## Run tests with coverage
	uv run pytest --cov=src --cov-report=html --cov-report=term

format: ## Format code with black and isort
	uv run black src tests
	uv run isort src tests

lint: ## Run linting with flake8 and mypy
	uv run flake8 src tests
	uv run mypy src

check: format lint test ## Run all quality checks

run: ## Run the development server
	uv run fastapi-todo-app

run-reload: ## Run the development server with auto-reload
	uv run uvicorn fastapi_todo_app.main:app --reload --host 0.0.0.0 --port 8000

clean: ## Clean cache and temporary files
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache
	rm -rf htmlcov
	rm -rf .coverage
	rm -rf dist
	rm -rf *.egg-info

docker-build: ## Build Docker image
	docker build -t fastapi-todo-app .

docker-run: ## Run Docker container
	docker run -p 8000:8000 fastapi-todo-app

update: ## Update dependencies
	uv lock --upgrade

build: ## Build the package
	uv build

publish: ## Publish the package (requires proper setup)
	uv publish

init-db: ## Initialize the database
	uv run python -c "from fastapi_todo_app.db.database import create_tables; create_tables()"