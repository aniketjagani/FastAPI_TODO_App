#!/bin/bash
# Production entrypoint script for FastAPI TODO application

set -e

echo "🚀 Starting FastAPI TODO Application..."

# Function to wait for database
wait_for_db() {
    echo "⏳ Waiting for database connection..."
    
    until python -c "
import psycopg2
import os
import sys
try:
    conn = psycopg2.connect(
        host=os.environ.get('DB_HOST', 'localhost'),
        port=os.environ.get('DB_PORT', '5432'),
        user=os.environ.get('DB_USER', 'postgres'),
        password=os.environ.get('DB_PASSWORD', ''),
        database=os.environ.get('DB_NAME', 'todos_db')
    )
    conn.close()
    print('✅ Database is ready!')
except psycopg2.OperationalError as e:
    print(f'❌ Database not ready: {e}')
    sys.exit(1)
"; do
        echo "📊 Database is unavailable - sleeping 2 seconds..."
        sleep 2
    done
}

# Function to run database migrations
run_migrations() {
    echo "📦 Running database migrations..."
    
    # Check if alembic is configured
    if [ -f "alembic.ini" ]; then
        uv run alembic upgrade head
        echo "✅ Database migrations completed"
    else
        echo "⚠️ No alembic configuration found, skipping migrations"
    fi
}

# Function to initialize application data
init_app_data() {
    echo "🔧 Initializing application data..."
    
    # Run any initialization scripts
    if [ -f "scripts/init_data.py" ]; then
        uv run python scripts/init_data.py
        echo "✅ Application data initialized"
    fi
}

# Main execution
main() {
    # Wait for external dependencies
    if [ "${WAIT_FOR_DB:-true}" = "true" ]; then
        wait_for_db
    fi
    
    # Run migrations if enabled
    if [ "${RUN_MIGRATIONS:-true}" = "true" ]; then
        run_migrations
    fi
    
    # Initialize application data if enabled
    if [ "${INIT_DATA:-false}" = "true" ]; then
        init_app_data
    fi
    
    echo "🎯 Starting application with command: $@"
    
    # Execute the main application command
    exec "$@"
}

# Run main function with all arguments
main "$@"