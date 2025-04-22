import os
import sqlite3
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker
from sync_databases import User, Dog, db
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

# Initialize Flask-SQLAlchemy
db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'user'  # Using singular form to match existing database
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    type = db.Column(db.String(20), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

class Dog(db.Model):
    __tablename__ = 'dog'  # Using singular form to match existing database
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    breed = db.Column(db.String(100), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    color = db.Column(db.String(100), nullable=False)
    height = db.Column(db.Float, nullable=False)
    weight = db.Column(db.Float, nullable=False)
    gender = db.Column(db.String(10), nullable=False)
    vaccines = db.Column(db.String(500))
    diseases = db.Column(db.String(500))
    medical_history = db.Column(db.String(1000))
    personality = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, nullable=False)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

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

def show_table_structure(engine, table_name):
    """Show the structure of a table"""
    inspector = inspect(engine)
    columns = inspector.get_columns(table_name)
    print(f"\nStructure of {table_name} table:")
    for column in columns:
        print(f"  {column['name']}: {column['type']}")

def check_database():
    print("\n=== Checking Database Contents ===")
    
    # Check SQLite database
    sqlite_engine = create_engine('sqlite:///instance/adoptease.db')
    SQLiteSession = sessionmaker(bind=sqlite_engine)
    sqlite_session = SQLiteSession()
    
    try:
        # Check if tables exist in SQLite
        inspector = inspect(sqlite_engine)
        existing_tables = inspector.get_table_names()
        
        if 'user' not in existing_tables:
            print("Creating user table in SQLite...")
            User.__table__.create(bind=sqlite_engine)
        if 'dog' not in existing_tables:
            print("Creating dog table in SQLite...")
            Dog.__table__.create(bind=sqlite_engine)
        
        # Show table structures
        show_table_structure(sqlite_engine, 'user')
        show_table_structure(sqlite_engine, 'dog')
        
        # Get counts
        sqlite_users = sqlite_session.query(User).count()
        sqlite_dogs = sqlite_session.query(Dog).count()
        print(f"\nSQLite counts - Users: {sqlite_users}, Dogs: {sqlite_dogs}")
        
    except Exception as e:
        print(f"Error checking SQLite database: {str(e)}")
    finally:
        sqlite_session.close()
    
    # Check PostgreSQL database if DATABASE_URL is set
    postgres_url = os.getenv('DATABASE_URL')
    if not postgres_url:
        print("\nDATABASE_URL not set. Please set it using:")
        print("export DATABASE_URL='postgresql://username:password@host:port/database'")
        print("or on Windows:")
        print("set DATABASE_URL=postgresql://username:password@host:port/database")
        print("\nYour current DATABASE_URL should be:")
        print("postgresql://adoptease_user:vF68HOLthnOVCugVi7hOVZ5BzSKp2GvQ@dpg-d040cb7gi27c73b51geg-a/adoptease")
        return
    
    # Convert postgres:// to postgresql:// if needed
    if postgres_url.startswith('postgres://'):
        postgres_url = postgres_url.replace('postgres://', 'postgresql://', 1)
    
    postgres_engine = create_engine(postgres_url)
    PostgreSQLSession = sessionmaker(bind=postgres_engine)
    postgres_session = PostgreSQLSession()
    
    try:
        # Check if tables exist in PostgreSQL
        inspector = inspect(postgres_engine)
        existing_tables = inspector.get_table_names()
        
        if 'user' not in existing_tables:
            print("Creating user table in PostgreSQL...")
            User.__table__.create(bind=postgres_engine)
        if 'dog' not in existing_tables:
            print("Creating dog table in PostgreSQL...")
            Dog.__table__.create(bind=postgres_engine)
        
        # Show table structures
        show_table_structure(postgres_engine, 'user')
        show_table_structure(postgres_engine, 'dog')
        
        # Get counts
        postgres_users = postgres_session.query(User).count()
        postgres_dogs = postgres_session.query(Dog).count()
        print(f"\nPostgreSQL counts - Users: {postgres_users}, Dogs: {postgres_dogs}")
        
    except Exception as e:
        print(f"Error checking PostgreSQL database: {str(e)}")
    finally:
        postgres_session.close()

if __name__ == "__main__":
    check_database() 