# Production-Ready FastAPI TODO Application
# Multi-stage Docker build for optimal performance and security

# Stage 1: Build stage
FROM python:3.13-slim-bookworm AS builder

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_CACHE_DIR=/tmp/uv-cache

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install UV (Python package manager)
RUN pip install uv

# Create app user
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Set work directory
WORKDIR /app

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies
RUN uv sync --frozen --no-dev

# Copy application code
COPY src/ ./src/
COPY scripts/ ./scripts/

# Build the application
RUN uv build

# Stage 2: Production stage
FROM python:3.13-slim-bookworm AS production

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PORT=8000

# Install runtime dependencies only
RUN apt-get update && apt-get install -y \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create app user
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Set work directory
WORKDIR /app

# Copy UV from builder stage
COPY --from=builder /usr/local/bin/uv /usr/local/bin/uv

# Copy built application and dependencies
COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app/src /app/src
COPY --from=builder /app/dist /app/dist

# Create directories for logs and data
RUN mkdir -p /app/logs /app/data && \
    chown -R appuser:appuser /app

# Copy configuration files
COPY docker/entrypoint.sh /entrypoint.sh
COPY docker/healthcheck.py /healthcheck.py

# Make scripts executable
RUN chmod +x /entrypoint.sh /healthcheck.py

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python /healthcheck.py

# Set entrypoint
ENTRYPOINT ["/entrypoint.sh"]

# Default command
CMD ["uv", "run", "uvicorn", "src.fastapi_todo_app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]