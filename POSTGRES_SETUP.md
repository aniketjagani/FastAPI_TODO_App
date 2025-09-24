# PostgreSQL Setup Guide for FastAPI Employee Management

This guide will help you set up PostgreSQL for the Employee Management system.

## Prerequisites

1. **PostgreSQL Installation**: Make sure PostgreSQL is installed and running on your system.
   
   ### Windows:
   - Download from: https://www.postgresql.org/download/windows/
   - During installation, remember your `postgres` user password
   
   ### macOS:
   ```bash
   brew install postgresql@15
   brew services start postgresql@15
   ```
   
   ### Ubuntu/Debian:
   ```bash
   sudo apt update
   sudo apt install postgresql postgresql-contrib
   sudo systemctl start postgresql
   ```

2. **Verify PostgreSQL is Running**:
   ```bash
   # Check if PostgreSQL is running
   pg_isready -h localhost -p 5432
   
   # Connect to PostgreSQL (you'll be prompted for password)
   psql -h localhost -U postgres -d postgres
   ```

## Database Setup

### Option 1: Automatic Setup (Recommended)

1. **Update Environment Variables**:
   Copy `.env.example` to `.env` and update the PostgreSQL settings:
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` file:
   ```bash
   # Employee Database (PostgreSQL)
   POSTGRES_DATABASE_URL=postgresql://postgres:your_password@localhost:5432/employees_db
   POSTGRES_HOST=localhost
   POSTGRES_PORT=5432
   POSTGRES_USER=postgres
   POSTGRES_PASSWORD=your_actual_password  # Replace with your PostgreSQL password
   POSTGRES_DB=employees_db
   ```

2. **Run the Setup Script**:
   ```bash
   # Install dependencies first
   uv sync
   
   # Run PostgreSQL setup
   uv run python scripts/setup_postgres.py
   ```

### Option 2: Manual Setup

1. **Connect to PostgreSQL**:
   ```bash
   psql -h localhost -U postgres -d postgres
   ```

2. **Create the Database**:
   ```sql
   CREATE DATABASE employees_db;
   \q
   ```

3. **Test Connection**:
   ```bash
   psql -h localhost -U postgres -d employees_db
   ```

## Configuration Options

### Environment Variables

All PostgreSQL settings can be configured via environment variables:

```bash
# Required Settings
POSTGRES_DATABASE_URL=postgresql://username:password@host:port/database
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password
POSTGRES_DB=employees_db

# Optional Connection Pool Settings
POSTGRES_POOL_SIZE=10
POSTGRES_MAX_OVERFLOW=20
POSTGRES_POOL_RECYCLE=3600

# Debug Settings
SQL_DEBUG=false  # Set to 'true' to see SQL queries in logs
```

### Connection Pool Configuration

The application uses SQLAlchemy connection pooling for optimal performance:

- **Pool Size**: 10 connections by default
- **Max Overflow**: 20 additional connections when needed
- **Pool Recycle**: Connections are recycled after 1 hour
- **Pre-ping**: Connections are tested before use

## Database Schema

The Employee management system uses the following PostgreSQL features:

### Tables Created:

1. **employees**: Main employee data table
   - Uses PostgreSQL ARRAY type for skills
   - Enum types for department, status, and employment type
   - Self-referencing foreign key for manager relationships
   - Automatic timestamp tracking

### PostgreSQL-Specific Features:

- **ARRAY columns** for storing employee skills
- **ENUM types** for department, status, and employment type
- **Self-referencing foreign keys** for manager-employee relationships
- **Automatic timestamps** with timezone support
- **Numeric precision** for salary fields

## Troubleshooting

### Common Issues:

1. **Connection Refused**:
   ```bash
   # Make sure PostgreSQL is running
   sudo systemctl status postgresql  # Linux
   brew services list | grep postgresql  # macOS
   ```

2. **Authentication Failed**:
   - Check your password in the `.env` file
   - Ensure the PostgreSQL user has the correct permissions

3. **Database Does Not Exist**:
   - Run the setup script: `uv run python scripts/setup_postgres.py`
   - Or create manually: `createdb -U postgres employees_db`

4. **Permission Denied**:
   ```sql
   -- Grant necessary permissions
   GRANT ALL PRIVILEGES ON DATABASE employees_db TO postgres;
   ```

### Verification Commands:

```bash
# Test PostgreSQL connection
uv run python -c "
from src.fastapi_todo_app.employees.db.database import engine
with engine.connect() as conn:
    result = conn.execute('SELECT version()')
    print('✅ PostgreSQL Connected:', result.fetchone()[0])
"

# Check database info
uv run python -c "
from src.fastapi_todo_app.employees.db.database import get_database_info
print(get_database_info())
"
```

## Running the Application

Once PostgreSQL is set up:

```bash
# Start the FastAPI application (both TODO and Employee apps)
uv run fastapi-todo-app

# The application will:
# 1. Create SQLite tables for TODOs
# 2. Create PostgreSQL tables for Employees
# 3. Start the server on http://localhost:8000
```

## API Endpoints

After setup, you'll have access to both applications:

### TODO Endpoints (SQLite):
- `GET /api/v1/todos/` - List todos
- `POST /api/v1/todos/` - Create todo
- And all other TODO operations...

### Employee Endpoints (PostgreSQL):
- `GET /api/v1/employees/` - List employees
- `POST /api/v1/employees/` - Create employee  
- `GET /api/v1/employees/stats` - Employee statistics
- `GET /api/v1/employees/department/{department}` - Filter by department
- And many more advanced operations...

### API Documentation:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Next Steps

1. ✅ Set up PostgreSQL
2. ✅ Configure environment variables
3. ✅ Run the setup script
4. ✅ Start the application
5. 🎉 Use both TODO and Employee management systems!

The dual-database architecture allows you to:
- Use SQLite for lightweight TODO operations
- Use PostgreSQL for complex employee management with advanced features
- Scale each system independently as needed