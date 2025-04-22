import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables from .env file
load_dotenv()

# Initialize Flask-SQLAlchemy
db = SQLAlchemy()

def add_updated_at_column():
    """Add updated_at column to existing tables"""
    print("\n=== Adding updated_at columns ===")
    
    # Create SQLite engine
    sqlite_engine = create_engine('sqlite:///instance/adoptease.db')
    SQLiteSession = sessionmaker(bind=sqlite_engine)
    sqlite_session = SQLiteSession()
    
    try:
        # For SQLite, we need to create a new table with the updated schema
        print("Updating SQLite tables...")
        
        # Create temporary tables with new schema
        sqlite_session.execute(text("""
            CREATE TABLE user_temp (
                id INTEGER PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                email VARCHAR(120) UNIQUE NOT NULL,
                password VARCHAR(200) NOT NULL,
                type VARCHAR(20) NOT NULL,
                created_at DATETIME NOT NULL,
                updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """))
        
        sqlite_session.execute(text("""
            CREATE TABLE dog_temp (
                id INTEGER PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                breed VARCHAR(100) NOT NULL,
                age INTEGER NOT NULL,
                color VARCHAR(100) NOT NULL,
                height FLOAT NOT NULL,
                weight FLOAT NOT NULL,
                gender VARCHAR(10) NOT NULL,
                vaccines VARCHAR(500),
                diseases VARCHAR(500),
                medical_history VARCHAR(1000),
                personality VARCHAR(500),
                created_at DATETIME NOT NULL,
                updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """))
        
        # Copy data from old tables to new tables
        current_time = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        
        sqlite_session.execute(text(f"""
            INSERT INTO user_temp (id, name, email, password, type, created_at, updated_at)
            SELECT id, name, email, password, type, created_at, '{current_time}'
            FROM user
        """))
        
        sqlite_session.execute(text(f"""
            INSERT INTO dog_temp (id, name, breed, age, color, height, weight, gender, 
                                vaccines, diseases, medical_history, personality, created_at, updated_at)
            SELECT id, name, breed, age, color, height, weight, gender, 
                   vaccines, diseases, medical_history, personality, created_at, '{current_time}'
            FROM dog
        """))
        
        # Drop old tables and rename new ones
        sqlite_session.execute(text("DROP TABLE user"))
        sqlite_session.execute(text("DROP TABLE dog"))
        sqlite_session.execute(text("ALTER TABLE user_temp RENAME TO user"))
        sqlite_session.execute(text("ALTER TABLE dog_temp RENAME TO dog"))
        
        sqlite_session.commit()
        print("Successfully updated SQLite tables with updated_at columns")
        
    except Exception as e:
        print(f"Error updating SQLite: {str(e)}")
        sqlite_session.rollback()
    finally:
        sqlite_session.close()
    
    # Update PostgreSQL if DATABASE_URL is set
    postgres_url = os.getenv('DATABASE_URL')
    if postgres_url:
        print("\nUpdating PostgreSQL tables...")
        if postgres_url.startswith('postgres://'):
            postgres_url = postgres_url.replace('postgres://', 'postgresql://', 1)
        
        postgres_engine = create_engine(postgres_url)
        PostgreSQLSession = sessionmaker(bind=postgres_engine)
        postgres_session = PostgreSQLSession()
        
        try:
            # Add updated_at to user table
            print("Adding updated_at to PostgreSQL user table...")
            postgres_session.execute(text("""
                ALTER TABLE "user" ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            """))
            
            # Add updated_at to dog table
            print("Adding updated_at to PostgreSQL dog table...")
            postgres_session.execute(text("""
                ALTER TABLE dog ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            """))
            
            postgres_session.commit()
            print("Successfully added updated_at columns to PostgreSQL")
            
        except Exception as e:
            print(f"Error updating PostgreSQL: {str(e)}")
            postgres_session.rollback()
        finally:
            postgres_session.close()

if __name__ == "__main__":
    add_updated_at_column() 