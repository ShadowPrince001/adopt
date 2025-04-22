import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

# Initialize Flask-SQLAlchemy
db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    type = db.Column(db.String(20), nullable=False)  # admin, customer, or expert
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Dog(db.Model):
    __tablename__ = 'dog'
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
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

def get_latest_timestamp(session, model):
    """Get the latest timestamp from a model's records"""
    try:
        latest = session.query(model).order_by(model.created_at.desc()).first()
        return latest.created_at if latest else datetime.min
    except Exception as e:
        print(f"Error getting latest timestamp: {str(e)}")
        return datetime.min

def sync_databases():
    print("\n=== Starting Database Synchronization ===")
    
    # Create both database engines
    sqlite_engine = create_engine('sqlite:///adoptease.db')
    postgres_engine = create_engine(os.getenv('DATABASE_URL'))
    
    print("Database engines created")
    
    # Create sessions
    SQLiteSession = sessionmaker(bind=sqlite_engine)
    PostgreSQLSession = sessionmaker(bind=postgres_engine)
    sqlite_session = SQLiteSession()
    postgres_session = PostgreSQLSession()

    try:
        print("\nCreating tables if they don't exist...")
        # Create tables in both databases
        User.__table__.create(bind=sqlite_engine, checkfirst=True)
        Dog.__table__.create(bind=sqlite_engine, checkfirst=True)
        User.__table__.create(bind=postgres_engine, checkfirst=True)
        Dog.__table__.create(bind=postgres_engine, checkfirst=True)
        print("Tables created/verified")

        # Get record counts from both databases
        sqlite_user_count = sqlite_session.query(User).count()
        sqlite_dog_count = sqlite_session.query(Dog).count()
        postgres_user_count = postgres_session.query(User).count()
        postgres_dog_count = postgres_session.query(Dog).count()

        print("\nCurrent Database State:")
        print(f"SQLite: {sqlite_user_count} users, {sqlite_dog_count} dogs")
        print(f"PostgreSQL: {postgres_user_count} users, {postgres_dog_count} dogs")

        # If SQLite has data and PostgreSQL is empty, sync from SQLite to PostgreSQL
        if sqlite_user_count > 0 and postgres_user_count == 0:
            print("\nPostgreSQL users table is empty, syncing from SQLite...")
            users = sqlite_session.query(User).all()
            print(f"Found {len(users)} users in SQLite to sync")
            for user in users:
                print(f"Syncing user: {user.email}")
                new_user = User(
                    name=user.name,
                    email=user.email,
                    password=user.password,
                    type=user.type,
                    created_at=user.created_at
                )
                postgres_session.add(new_user)
            postgres_session.commit()
            print(f"Synced {len(users)} users from SQLite to PostgreSQL")

        if sqlite_dog_count > 0 and postgres_dog_count == 0:
            print("\nPostgreSQL dogs table is empty, syncing from SQLite...")
            dogs = sqlite_session.query(Dog).all()
            print(f"Found {len(dogs)} dogs in SQLite to sync")
            for dog in dogs:
                print(f"Syncing dog: {dog.name} ({dog.breed})")
                new_dog = Dog(
                    name=dog.name,
                    breed=dog.breed,
                    age=dog.age,
                    color=dog.color,
                    height=dog.height,
                    weight=dog.weight,
                    gender=dog.gender,
                    vaccines=dog.vaccines,
                    diseases=dog.diseases,
                    medical_history=dog.medical_history,
                    personality=dog.personality,
                    created_at=dog.created_at
                )
                postgres_session.add(new_dog)
            postgres_session.commit()
            print(f"Synced {len(dogs)} dogs from SQLite to PostgreSQL")

        # Verify the sync
        print("\nVerifying sync results...")
        final_sqlite_user_count = sqlite_session.query(User).count()
        final_sqlite_dog_count = sqlite_session.query(Dog).count()
        final_postgres_user_count = postgres_session.query(User).count()
        final_postgres_dog_count = postgres_session.query(Dog).count()

        print("\nFinal Database State:")
        print(f"SQLite: {final_sqlite_user_count} users, {final_sqlite_dog_count} dogs")
        print(f"PostgreSQL: {final_postgres_user_count} users, {final_postgres_dog_count} dogs")

        if final_postgres_dog_count == 0 and sqlite_dog_count > 0:
            print("\nWARNING: Dogs were not synced to PostgreSQL!")
            print("Attempting manual sync...")
            dogs = sqlite_session.query(Dog).all()
            for dog in dogs:
                try:
                    new_dog = Dog(
                        name=dog.name,
                        breed=dog.breed,
                        age=dog.age,
                        color=dog.color,
                        height=dog.height,
                        weight=dog.weight,
                        gender=dog.gender,
                        vaccines=dog.vaccines,
                        diseases=dog.diseases,
                        medical_history=dog.medical_history,
                        personality=dog.personality,
                        created_at=dog.created_at
                    )
                    postgres_session.add(new_dog)
                except Exception as e:
                    print(f"Error syncing dog {dog.name}: {str(e)}")
            postgres_session.commit()
            print("Manual sync attempt completed")

        print("\n=== Database Synchronization Completed ===")

    except Exception as e:
        print(f"\nERROR during synchronization: {str(e)}")
        postgres_session.rollback()
        sqlite_session.rollback()
        raise

    finally:
        postgres_session.close()
        sqlite_session.close()

if __name__ == "__main__":
    sync_databases() 