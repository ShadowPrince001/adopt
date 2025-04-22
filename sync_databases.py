import os
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

# Initialize Flask-SQLAlchemy
db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'user'  # Changed from 'users' to 'user'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    type = db.Column(db.String(20), nullable=False)  # admin, customer, or expert
    created_at = db.Column(db.DateTime, nullable=False)

class Dog(db.Model):
    __tablename__ = 'dog'  # Changed from 'dogs' to 'dog'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    breed = db.Column(db.String(100), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    color = db.Column(db.String(100), nullable=False)
    height = db.Column(db.Float, nullable=False)  # in cm
    weight = db.Column(db.Float, nullable=False)  # in kg
    gender = db.Column(db.String(10), nullable=False)  # Male or Female
    vaccines = db.Column(db.String(500))
    diseases = db.Column(db.String(500))
    medical_history = db.Column(db.String(1000))
    personality = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, nullable=False)

def check_existing_tables(engine):
    """Check what tables exist in the database"""
    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()
    print(f"\nExisting tables: {existing_tables}")
    return existing_tables

def create_tables(engine):
    """Create tables if they don't exist"""
    existing_tables = check_existing_tables(engine)
    
    if 'user' not in existing_tables:  # Updated to match new table name
        print("Creating user table...")
        User.__table__.create(bind=engine)
    
    if 'dog' not in existing_tables:  # Updated to match new table name
        print("Creating dog table...")
        Dog.__table__.create(bind=engine)

def get_latest_timestamp(session, model):
    """Get the latest timestamp from a model's records"""
    try:
        latest = session.query(model).order_by(model.created_at.desc()).first()
        return latest.created_at if latest else datetime.min
    except Exception as e:
        print(f"Error getting latest timestamp: {str(e)}")
        return datetime.min

def sync_databases():
    """Synchronize data between SQLite and PostgreSQL databases"""
    print("\n=== Starting Database Synchronization ===")
    
    # Create SQLite engine
    sqlite_engine = create_engine('sqlite:///instance/adoptease.db')  # Updated to use instance path
    SQLiteSession = sessionmaker(bind=sqlite_engine)
    sqlite_session = SQLiteSession()
    
    # Create PostgreSQL engine if DATABASE_URL is set
    postgres_url = os.getenv('DATABASE_URL')
    if postgres_url:
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
            
            print(f"\nSQLite counts - Users: {sqlite_users}, Dogs: {sqlite_dogs}")
            print(f"PostgreSQL counts - Users: {postgres_users}, Dogs: {postgres_dogs}")
            
            # Sync from SQLite to PostgreSQL if PostgreSQL is empty
            if postgres_users == 0 and sqlite_users > 0:
                print("\nSyncing users from SQLite to PostgreSQL...")
                users = sqlite_session.query(User).all()
                for user in users:
                    postgres_session.merge(user)
                postgres_session.commit()
                print(f"Synced {len(users)} users")
            
            if postgres_dogs == 0 and sqlite_dogs > 0:
                print("\nSyncing dogs from SQLite to PostgreSQL...")
                dogs = sqlite_session.query(Dog).all()
                for dog in dogs:
                    postgres_session.merge(dog)
                postgres_session.commit()
                print(f"Synced {len(dogs)} dogs")
            
            # Verify final counts
            final_postgres_users = postgres_session.query(User).count()
            final_postgres_dogs = postgres_session.query(Dog).count()
            print(f"\nFinal PostgreSQL counts - Users: {final_postgres_users}, Dogs: {final_postgres_dogs}")
            
        except Exception as e:
            print(f"Error during synchronization: {str(e)}")
            postgres_session.rollback()
        finally:
            postgres_session.close()
    else:
        print("\nDATABASE_URL not set, skipping PostgreSQL synchronization")
    
    sqlite_session.close()
    print("\n=== Database Synchronization Complete ===")

if __name__ == "__main__":
    sync_databases() 