import os
import sqlite3
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker
from sync_databases import User, Dog, db

def check_sqlite_directly(db_path):
    """Check SQLite database directly using sqlite3"""
    print(f"\n=== Direct SQLite Database Check ===")
    print(f"Database file path: {os.path.abspath(db_path)}")
    print(f"Database file exists: {os.path.exists(db_path)}")
    if os.path.exists(db_path):
        print(f"Database file size: {os.path.getsize(db_path)} bytes")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print("\nAll tables in database:")
        for table in tables:
            print(f"- {table[0]}")
        
        # For each table, show structure and count
        for table in tables:
            table_name = table[0]
            print(f"\nTable: {table_name}")
            
            # Get table structure
            cursor.execute(f"PRAGMA table_info({table_name});")
            columns = cursor.fetchall()
            print("Structure:")
            for col in columns:
                print(f"- {col[1]} ({col[2]})")
            
            # Get row count
            cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
            count = cursor.fetchone()[0]
            print(f"Total rows: {count}")
            
            # Show first few rows
            if count > 0:
                cursor.execute(f"SELECT * FROM {table_name} LIMIT 5;")
                rows = cursor.fetchall()
                print("\nFirst few rows:")
                for row in rows:
                    print(row)
            else:
                print("No rows found in table")
        
    except Exception as e:
        print(f"Error checking SQLite directly: {str(e)}")
    finally:
        if 'conn' in locals():
            conn.close()

def check_databases():
    print("\n=== Checking Database Contents ===")
    
    # Only check the instance database as it's the one with data
    instance_db_path = os.path.join('instance', 'adoptease.db')
    print(f"\nChecking database at: {instance_db_path}")
    check_sqlite_directly(instance_db_path)
    
    # Then check using SQLAlchemy
    print("\n=== SQLAlchemy Database Check ===")
    
    # Only check the instance database with SQLAlchemy
    print(f"\nChecking SQLite Database with SQLAlchemy at: {instance_db_path}")
    sqlite_engine = create_engine(f'sqlite:///{instance_db_path}')
    SQLiteSession = sessionmaker(bind=sqlite_engine)
    sqlite_session = SQLiteSession()
    
    try:
        # First check what tables exist
        inspector = inspect(sqlite_engine)
        existing_tables = inspector.get_table_names()
        print(f"\nExisting tables: {existing_tables}")
        
        # Show table structure
        for table_name in existing_tables:
            print(f"\nStructure of table '{table_name}':")
            columns = inspector.get_columns(table_name)
            for column in columns:
                print(f"- {column['name']}: {column['type']}")
        
        # Query users
        try:
            users = sqlite_session.query(User).all()
            print(f"\nUsers in SQLite ({len(users)}):")
            for user in users:
                print(f"- {user.email} ({user.type})")
        except Exception as e:
            print(f"Error querying users: {str(e)}")
        
        # Query dogs
        try:
            dogs = sqlite_session.query(Dog).all()
            print(f"\nDogs in SQLite ({len(dogs)}):")
            for dog in dogs:
                print(f"- {dog.name} ({dog.breed}, {dog.gender})")
        except Exception as e:
            print(f"Error querying dogs: {str(e)}")
                
    except Exception as e:
        print(f"Error checking SQLite with SQLAlchemy: {str(e)}")
    finally:
        sqlite_session.close()
    
    # Check PostgreSQL database
    print("\nChecking PostgreSQL Database:")
    postgres_url = os.getenv('DATABASE_URL')
    if postgres_url:
        # Convert postgres:// to postgresql:// if needed
        if postgres_url.startswith('postgres://'):
            postgres_url = postgres_url.replace('postgres://', 'postgresql://', 1)
        postgres_engine = create_engine(postgres_url)
        PostgreSQLSession = sessionmaker(bind=postgres_engine)
        postgres_session = PostgreSQLSession()
        
        try:
            # First check what tables exist
            inspector = inspect(postgres_engine)
            existing_tables = inspector.get_table_names()
            print(f"\nExisting tables: {existing_tables}")
            
            # Show table structure
            for table_name in existing_tables:
                print(f"\nStructure of table '{table_name}':")
                columns = inspector.get_columns(table_name)
                for column in columns:
                    print(f"- {column['name']}: {column['type']}")
            
            # Query users
            try:
                users = postgres_session.query(User).all()
                print(f"\nUsers in PostgreSQL ({len(users)}):")
                for user in users:
                    print(f"- {user.email} ({user.type})")
            except Exception as e:
                print(f"Error querying users: {str(e)}")
            
            # Query dogs
            try:
                dogs = postgres_session.query(Dog).all()
                print(f"\nDogs in PostgreSQL ({len(dogs)}):")
                for dog in dogs:
                    print(f"- {dog.name} ({dog.breed}, {dog.gender})")
            except Exception as e:
                print(f"Error querying dogs: {str(e)}")
                    
        except Exception as e:
            print(f"Error checking PostgreSQL: {str(e)}")
            print("Make sure your DATABASE_URL is correct and the database is accessible.")
        finally:
            postgres_session.close()
    else:
        print("\nDATABASE_URL not set, skipping PostgreSQL check")

if __name__ == "__main__":
    check_databases() 