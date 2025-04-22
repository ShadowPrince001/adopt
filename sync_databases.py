import os
import time
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
import sys

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

def sync_databases():
    """Synchronize data from PostgreSQL to SQLite database"""
    print("\n=== Starting Database Synchronization ===")
    print("Note: In Render's free tier, SQLite is ephemeral and will be reset on redeployment.")
    print("This sync ensures SQLite has the latest data from PostgreSQL after each deployment.")
    
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
        
        # Track changes
        users_added = 0
        users_updated = 0
        dogs_added = 0
        dogs_updated = 0
        
        # Sync users from PostgreSQL to SQLite
        print("\n=== Syncing users from PostgreSQL to SQLite ===")
        postgres_users_list = postgres_session.query(User).all()
        sqlite_users_map = {user.email: user for user in sqlite_session.query(User).all()}
        
        for postgres_user in postgres_users_list:
            if postgres_user.email not in sqlite_users_map:
                print(f"Adding new user to SQLite: {postgres_user.email}")
                sqlite_session.merge(postgres_user)
                users_added += 1
            else:
                sqlite_user = sqlite_users_map[postgres_user.email]
                if postgres_user.updated_at > sqlite_user.updated_at:
                    print(f"Updating user in SQLite: {postgres_user.email}")
                    sqlite_session.merge(postgres_user)
                    users_updated += 1
        
        # Sync dogs from PostgreSQL to SQLite
        print("\n=== Syncing dogs from PostgreSQL to SQLite ===")
        postgres_dogs_list = postgres_session.query(Dog).all()
        
        def get_dog_key(dog):
            return f"{dog.name}_{dog.breed}_{dog.age}"
        
        sqlite_dogs_map = {get_dog_key(dog): dog for dog in sqlite_session.query(Dog).all()}
        
        for postgres_dog in postgres_dogs_list:
            dog_key = get_dog_key(postgres_dog)
            if dog_key not in sqlite_dogs_map:
                print(f"Adding new dog to SQLite: {postgres_dog.name}")
                sqlite_session.merge(postgres_dog)
                dogs_added += 1
            else:
                sqlite_dog = sqlite_dogs_map[dog_key]
                if postgres_dog.updated_at > sqlite_dog.updated_at:
                    print(f"Updating dog in SQLite: {postgres_dog.name}")
                    sqlite_session.merge(postgres_dog)
                    dogs_updated += 1
        
        # Commit all changes
        sqlite_session.commit()
        
        # Print sync summary
        print("\n=== Sync Summary ===")
        print(f"Users: {users_added} added, {users_updated} updated")
        print(f"Dogs: {dogs_added} added, {dogs_updated} updated")
        
        # Verify final counts
        final_sqlite_users = sqlite_session.query(User).count()
        final_sqlite_dogs = sqlite_session.query(Dog).count()
        
        print(f"\nFinal counts:")
        print(f"SQLite - Users: {final_sqlite_users}, Dogs: {final_sqlite_dogs}")
        print(f"PostgreSQL - Users: {postgres_users}, Dogs: {postgres_dogs}")
        
        if users_added > 0 or users_updated > 0 or dogs_added > 0 or dogs_updated > 0:
            print("\nSQLite database has been updated with latest data from PostgreSQL.")
        else:
            print("\nNo changes needed - SQLite is already in sync with PostgreSQL.")
        
    except Exception as e:
        print(f"Error during synchronization: {str(e)}")
        sqlite_session.rollback()
    finally:
        postgres_session.close()
        sqlite_session.close()
    
    print("\n=== Database Synchronization Complete ===")

def run_continuous_sync(interval_seconds=300):  # Default 5 minutes
    """Run sync continuously at specified intervals"""
    print(f"Starting continuous sync with {interval_seconds} second interval...")
    print("This process will keep SQLite in sync with PostgreSQL.")
    print("In Render's free tier, SQLite is ephemeral and will be reset on redeployment.")
    print("The sync ensures SQLite has the latest data after each deployment.")
    
    while True:
        try:
            sync_databases()
            print(f"\nNext sync in {interval_seconds} seconds...")
            time.sleep(interval_seconds)
        except KeyboardInterrupt:
            print("\nStopping continuous sync...")
            break
        except Exception as e:
            print(f"Error in continuous sync: {str(e)}")
            print("Retrying in 60 seconds...")
            time.sleep(60)

if __name__ == "__main__":
    # Check if continuous sync is requested
    if len(sys.argv) > 1 and sys.argv[1] == "--continuous":
        run_continuous_sync()
    else:
        sync_databases() 