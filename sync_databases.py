import os
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

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

def sync_databases():
    """Synchronize data between SQLite and PostgreSQL databases"""
    print("\n=== Starting Database Synchronization ===")
    
    # Create SQLite engine
    sqlite_engine = create_engine('sqlite:///instance/adoptease.db')
    SQLiteSession = sessionmaker(bind=sqlite_engine)
    sqlite_session = SQLiteSession()
    
    # Get PostgreSQL URL from environment
    postgres_url = os.getenv('DATABASE_URL')
    
    if not postgres_url:
        print("\nDATABASE_URL not found in environment variables.")
        return
    
    # Convert postgres:// to postgresql:// if needed
    if postgres_url.startswith('postgres://'):
        postgres_url = postgres_url.replace('postgres://', 'postgresql://', 1)
    
    postgres_engine = create_engine(postgres_url)
    PostgreSQLSession = sessionmaker(bind=postgres_engine)
    postgres_session = PostgreSQLSession()
    
    try:
        # Check if tables exist in PostgreSQL, create if they don't
        inspector = inspect(postgres_engine)
        existing_tables = inspector.get_table_names()
        
        if 'user' not in existing_tables:
            print("Creating user table in PostgreSQL...")
            User.__table__.create(bind=postgres_engine)
        if 'dog' not in existing_tables:
            print("Creating dog table in PostgreSQL...")
            Dog.__table__.create(bind=postgres_engine)
        
        # Get counts from both databases
        sqlite_users = sqlite_session.query(User).count()
        sqlite_dogs = sqlite_session.query(Dog).count()
        postgres_users = postgres_session.query(User).count()
        postgres_dogs = postgres_session.query(Dog).count()
        
        print(f"\nInitial counts:")
        print(f"SQLite - Users: {sqlite_users}, Dogs: {sqlite_dogs}")
        print(f"PostgreSQL - Users: {postgres_users}, Dogs: {postgres_dogs}")
        
        # Sync users with conflict resolution
        print("\nSyncing users...")
        sqlite_users_list = sqlite_session.query(User).all()
        postgres_users_list = postgres_session.query(User).all()
        
        # Create a map of users by email for quick lookup
        postgres_users_map = {user.email: user for user in postgres_users_list}
        sqlite_users_map = {user.email: user for user in sqlite_users_list}
        
        # Sync from SQLite to PostgreSQL
        for email, sqlite_user in sqlite_users_map.items():
            if email not in postgres_users_map:
                print(f"Adding new user to PostgreSQL: {email}")
                postgres_session.merge(sqlite_user)
            else:
                # Compare timestamps and update if SQLite is newer
                postgres_user = postgres_users_map[email]
                if sqlite_user.created_at > postgres_user.created_at:
                    print(f"Updating user in PostgreSQL (SQLite has newer data): {email}")
                    postgres_session.merge(sqlite_user)
        
        # Sync from PostgreSQL to SQLite
        for email, postgres_user in postgres_users_map.items():
            if email not in sqlite_users_map:
                print(f"Adding new user to SQLite: {email}")
                sqlite_session.merge(postgres_user)
            else:
                # Always use PostgreSQL data in case of conflict
                sqlite_user = sqlite_users_map[email]
                if postgres_user.created_at >= sqlite_user.created_at:
                    print(f"Updating user in SQLite (PostgreSQL has newer/equal data): {email}")
                    sqlite_session.merge(postgres_user)
        
        # Sync dogs with conflict resolution
        print("\nSyncing dogs...")
        sqlite_dogs_list = sqlite_session.query(Dog).all()
        postgres_dogs_list = postgres_session.query(Dog).all()
        
        # Create a map of dogs by unique identifier (name + breed + age)
        def get_dog_key(dog):
            return f"{dog.name}_{dog.breed}_{dog.age}"
        
        postgres_dogs_map = {get_dog_key(dog): dog for dog in postgres_dogs_list}
        sqlite_dogs_map = {get_dog_key(dog): dog for dog in sqlite_dogs_list}
        
        # Sync from SQLite to PostgreSQL
        for dog_key, sqlite_dog in sqlite_dogs_map.items():
            if dog_key not in postgres_dogs_map:
                print(f"Adding new dog to PostgreSQL: {sqlite_dog.name}")
                postgres_session.merge(sqlite_dog)
            else:
                # Compare timestamps and update if SQLite is newer
                postgres_dog = postgres_dogs_map[dog_key]
                if sqlite_dog.created_at > postgres_dog.created_at:
                    print(f"Updating dog in PostgreSQL (SQLite has newer data): {sqlite_dog.name}")
                    postgres_session.merge(sqlite_dog)
        
        # Sync from PostgreSQL to SQLite
        for dog_key, postgres_dog in postgres_dogs_map.items():
            if dog_key not in sqlite_dogs_map:
                print(f"Adding new dog to SQLite: {postgres_dog.name}")
                sqlite_session.merge(postgres_dog)
            else:
                # Always use PostgreSQL data in case of conflict
                sqlite_dog = sqlite_dogs_map[dog_key]
                if postgres_dog.created_at >= sqlite_dog.created_at:
                    print(f"Updating dog in SQLite (PostgreSQL has newer/equal data): {postgres_dog.name}")
                    sqlite_session.merge(postgres_dog)
        
        # Commit all changes
        postgres_session.commit()
        sqlite_session.commit()
        
        # Verify final counts
        final_sqlite_users = sqlite_session.query(User).count()
        final_sqlite_dogs = sqlite_session.query(Dog).count()
        final_postgres_users = postgres_session.query(User).count()
        final_postgres_dogs = postgres_session.query(Dog).count()
        
        print(f"\nFinal counts:")
        print(f"SQLite - Users: {final_sqlite_users}, Dogs: {final_sqlite_dogs}")
        print(f"PostgreSQL - Users: {final_postgres_users}, Dogs: {final_postgres_dogs}")
        
    except Exception as e:
        print(f"Error during synchronization: {str(e)}")
        postgres_session.rollback()
        sqlite_session.rollback()
    finally:
        postgres_session.close()
        sqlite_session.close()
    
    print("\n=== Database Synchronization Complete ===")

if __name__ == "__main__":
    sync_databases() 