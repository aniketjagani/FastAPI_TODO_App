"""
Setup script to create the todos_db database in PostgreSQL
"""

import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from urllib.parse import quote_plus
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


def create_todo_database():
    """
    Create the todos_db database if it doesn't exist
    """
    # Database configuration
    POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
    POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")  
    POSTGRES_USER = os.getenv("POSTGRES_USER", "aniketjagani")
    POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "adminaniket")
    TODO_DB = os.getenv("TODO_DB", "todos_db")
    
    # URL encode the password to handle special characters
    encoded_password = quote_plus(POSTGRES_PASSWORD)
    
    # Connection URL to postgres database (not the target database)
    admin_url = f"postgresql://{POSTGRES_USER}:{encoded_password}@{POSTGRES_HOST}:{POSTGRES_PORT}/postgres"
    
    # Connection URL to target database
    target_url = f"postgresql://{POSTGRES_USER}:{encoded_password}@{POSTGRES_HOST}:{POSTGRES_PORT}/{TODO_DB}"
    
    try:
        print("🔗 Connecting to PostgreSQL server...")
        
        # Connect to PostgreSQL server
        admin_engine = create_engine(admin_url)
        
        with admin_engine.connect() as conn:
            # Set autocommit for database creation
            conn.execute(text("COMMIT"))
            
            # Check if database exists
            result = conn.execute(
                text("SELECT 1 FROM pg_database WHERE datname = :db_name"),
                {"db_name": TODO_DB}
            )
            
            if result.fetchone():
                print(f"✅ Database '{TODO_DB}' already exists")
            else:
                # Create database
                conn.execute(text(f'CREATE DATABASE "{TODO_DB}"'))
                print(f"✅ Database '{TODO_DB}' created successfully")
        
        admin_engine.dispose()
        
        # Test connection to the new database
        print("🧪 Testing connection to todos database...")
        target_engine = create_engine(target_url)
        
        with target_engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            version = result.fetchone()[0]
            print(f"✅ Successfully connected to PostgreSQL: {version}")
        
        target_engine.dispose()
        
        return True
        
    except SQLAlchemyError as e:
        print(f"❌ Database error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False


def main():
    """
    Main setup function
    """
    print("📋 PostgreSQL TODO Database Setup")
    print("=" * 50)
    
    # Create database
    if create_todo_database():
        print("✅ TODO database setup completed successfully!")
        print("\n🎉 You now have separate PostgreSQL databases:")
        print("- todos_db: For TODO management")
        print("- employees_db: For Employee management")
        print("\n📝 Next step: Run the FastAPI application with: uv run fastapi-todo-app")
    else:
        print("❌ TODO database setup failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()