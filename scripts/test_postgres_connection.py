"""
Simple PostgreSQL Connection Test
"""

import os
from sqlalchemy import create_engine, text
from urllib.parse import quote_plus


def test_connection_with_password(password):
    """
    Test PostgreSQL connection with a specific password
    """
    # URL encode the password to handle special characters
    encoded_password = quote_plus(password)
    
    # Create connection URL
    db_url = f"postgresql://postgres:{encoded_password}@localhost:5432/postgres"
    
    print(f"Testing connection with password: {password}")
    print(f"Encoded URL: postgresql://postgres:{encoded_password}@localhost:5432/postgres")
    
    try:
        engine = create_engine(db_url)
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            version = result.fetchone()[0]
            print(f"✅ SUCCESS! Connected to PostgreSQL: {version.split(' ')[0]} {version.split(' ')[1]}")
            
            # Test creating database
            try:
                conn.execute(text("COMMIT"))  # End any transaction
                result = conn.execute(text("SELECT 1 FROM pg_database WHERE datname = 'employees_db'"))
                if result.fetchone():
                    print("✅ Database 'employees_db' already exists")
                else:
                    conn.execute(text('CREATE DATABASE "employees_db"'))
                    print("✅ Database 'employees_db' created successfully")
            except Exception as e:
                print(f"⚠️  Database creation info: {e}")
            
            return True
            
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False
    finally:
        if 'engine' in locals():
            engine.dispose()


def main():
    """
    Test various password formats
    """
    print("🐘 PostgreSQL Connection Testing")
    print("=" * 50)
    
    # Test different password possibilities
    passwords_to_test = [
        "Admin@1234",  # Your current password
        "admin@1234",  # lowercase version
        "password",    # default
        "postgres",    # common default
    ]
    
    success = False
    for password in passwords_to_test:
        print(f"\n🔍 Testing password: '{password}'")
        print("-" * 30)
        if test_connection_with_password(password):
            success = True
            print(f"\n🎉 SUCCESS! Working password is: '{password}'")
            break
        print()
    
    if not success:
        print("\n❌ None of the passwords worked. Please check:")
        print("1. PostgreSQL is running")
        print("2. The correct password for 'postgres' user")
        print("3. PostgreSQL is accepting connections on localhost:5432")
        print("\nYou can also try connecting manually:")
        print("psql -h localhost -U postgres -d postgres")


if __name__ == "__main__":
    main()