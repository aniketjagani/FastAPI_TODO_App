"""
PostgreSQL Database Setup Script for Employees App
"""

import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from urllib.parse import quote_plus
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


def create_database():
    """
    Create the employees_db database if it doesn't exist
    """
    # Database configuration
    POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
    POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")  
    POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
    POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "password")
    POSTGRES_DB = os.getenv("POSTGRES_DB", "employees_db")
    
    # URL encode the password to handle special characters
    encoded_password = quote_plus(POSTGRES_PASSWORD)
    
    # Connection URL to postgres database (not the target database)
    admin_url = f"postgresql://{POSTGRES_USER}:{encoded_password}@{POSTGRES_HOST}:{POSTGRES_PORT}/postgres"
    
    # Connection URL to target database
    target_url = f"postgresql://{POSTGRES_USER}:{encoded_password}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
    
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
                {"db_name": POSTGRES_DB}
            )
            
            if result.fetchone():
                print(f"✅ Database '{POSTGRES_DB}' already exists")
            else:
                # Create database
                conn.execute(text(f'CREATE DATABASE "{POSTGRES_DB}"'))
                print(f"✅ Database '{POSTGRES_DB}' created successfully")
        
        admin_engine.dispose()
        
        # Test connection to the new database
        print("🧪 Testing connection to employees database...")
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


def test_connection():
    """
    Test connection to the employees database
    """
    # Get connection details
    POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
    POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")  
    POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
    POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "password")
    POSTGRES_DB = os.getenv("POSTGRES_DB", "employees_db")
    
    # URL encode password
    encoded_password = quote_plus(POSTGRES_PASSWORD)
    POSTGRES_DATABASE_URL = f"postgresql://{POSTGRES_USER}:{encoded_password}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
    
    try:
        print("🧪 Testing PostgreSQL connection...")
        engine = create_engine(POSTGRES_DATABASE_URL)
        
        with engine.connect() as conn:
            result = conn.execute(text("SELECT current_database(), current_user, version()"))
            db_info = result.fetchone()
            
            print(f"✅ Connected to database: {db_info[0]}")
            print(f"✅ Connected as user: {db_info[1]}")
            print(f"✅ PostgreSQL version: {db_info[2].split(' ')[0]} {db_info[2].split(' ')[1]}")
        
        engine.dispose()
        return True
        
    except SQLAlchemyError as e:
        print(f"❌ Connection failed: {e}")
        return False


def main():
    """
    Main setup function
    """
    print("🐘 PostgreSQL Database Setup for FastAPI Employee App")
    print("=" * 60)
    
    # Create database
    if create_database():
        print("✅ Database setup completed successfully!")
    else:
        print("❌ Database setup failed!")
        sys.exit(1)
    
    # Test connection
    if test_connection():
        print("✅ Connection test passed!")
    else:
        print("❌ Connection test failed!")
        sys.exit(1)
    
    print("\n🎉 PostgreSQL setup completed! You can now start the FastAPI application.")
    print("\n📝 Next steps:")
    print("1. Make sure PostgreSQL is running on your system")
    print("2. Update the .env file with your PostgreSQL credentials")
    print("3. Run the FastAPI application with: uv run fastapi-todo-app")


if __name__ == "__main__":
    main()