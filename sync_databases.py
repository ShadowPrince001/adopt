import os
import time
from sqlalchemy import create_engine, inspect, text
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
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    type = db.Column(db.String(20), nullable=False)
    created_at = db.Column(db.DateTime, nullable=True)
    updated_at = db.Column(db.DateTime, nullable=True)

class Dog(db.Model):
    __tablename__ = 'dog'
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
    updated_at = db.Column(db.DateTime, nullable=True)

def initialize_sqlite_database():
    """Initialize SQLite database with proper schema"""
    print("\n=== Initializing SQLite Database ===")
    
    # Create SQLite engine
    sqlite_engine = create_engine('sqlite:///instance/adoptease.db')
    SQLiteSession = sessionmaker(bind=sqlite_engine)
    sqlite_session = SQLiteSession()
    
    try:
        # Drop existing tables if they exist
        sqlite_session.execute(text('DROP TABLE IF EXISTS user'))
        sqlite_session.execute(text('DROP TABLE IF EXISTS dog'))
        sqlite_session.commit()
        
        # Create tables with proper schema
        User.__table__.create(bind=sqlite_engine)
        Dog.__table__.create(bind=sqlite_engine)
        
        print("SQLite database initialized successfully")
        return True
    except Exception as e:
        print(f"Error initializing SQLite database: {str(e)}")
        sqlite_session.rollback()
        return False
    finally:
        sqlite_session.close()

def sync_databases():
    """Synchronize data from PostgreSQL to SQLite database"""
    print("\n=== Starting Database Synchronization ===")
    print("Note: In Render's free tier, SQLite is ephemeral and will be reset on redeployment.")
    print("This sync ensures SQLite has the latest data from PostgreSQL after each deployment.")
    
    # Initialize SQLite database first
    if not initialize_sqlite_database():
        print("Failed to initialize SQLite database. Aborting sync.")
        return
    
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
        for postgres_user in postgres_session.query(User).all():
            try:
                existing_user = sqlite_session.query(User).filter_by(id=postgres_user.id).first()
                current_time = datetime.utcnow()
                
                if existing_user:
                    # Update existing user
                    for key, value in postgres_user.__dict__.items():
                        if not key.startswith('_'):
                            setattr(existing_user, key, value)
                    existing_user.updated_at = current_time
                    users_updated += 1
                else:
                    # Add new user
                    new_user = User(
                        id=postgres_user.id,
                        name=postgres_user.name,
                        email=postgres_user.email,
                        password=postgres_user.password,
                        type=postgres_user.type,
                        created_at=postgres_user.created_at,
                        updated_at=current_time
                    )
                    sqlite_session.add(new_user)
                    users_added += 1
            except Exception as e:
                print(f"Error syncing user {postgres_user.id}: {str(e)}")
                continue
        
        # Sync dogs from PostgreSQL to SQLite
        print("\n=== Syncing dogs from PostgreSQL to SQLite ===")
        for postgres_dog in postgres_session.query(Dog).all():
            try:
                existing_dog = sqlite_session.query(Dog).filter_by(id=postgres_dog.id).first()
                current_time = datetime.utcnow()
                
                if existing_dog:
                    # Update existing dog
                    for key, value in postgres_dog.__dict__.items():
                        if not key.startswith('_'):
                            setattr(existing_dog, key, value)
                    existing_dog.updated_at = current_time
                    dogs_updated += 1
                else:
                    # Add new dog
                    new_dog = Dog(
                        id=postgres_dog.id,
                        name=postgres_dog.name,
                        breed=postgres_dog.breed,
                        age=postgres_dog.age,
                        color=postgres_dog.color,
                        height=postgres_dog.height,
                        weight=postgres_dog.weight,
                        gender=postgres_dog.gender,
                        vaccines=postgres_dog.vaccines,
                        diseases=postgres_dog.diseases,
                        medical_history=postgres_dog.medical_history,
                        personality=postgres_dog.personality,
                        created_at=postgres_dog.created_at,
                        updated_at=current_time
                    )
                    sqlite_session.add(new_dog)
                    dogs_added += 1
            except Exception as e:
                print(f"Error syncing dog {postgres_dog.id}: {str(e)}")
                continue
        
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