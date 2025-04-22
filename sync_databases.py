import os
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.orm import sessionmaker, declarative_base
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    email = Column(String(120), unique=True, nullable=False)
    password = Column(String(200), nullable=False)
    type = Column(String(20), nullable=False)  # admin, customer, or expert
    created_at = Column(DateTime, default=datetime.utcnow)

class Dog(Base):
    __tablename__ = 'dog'
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    breed = Column(String(100), nullable=False)
    age = Column(Integer, nullable=False)
    color = Column(String(100), nullable=False)
    height = Column(Float, nullable=False)  # in cm
    weight = Column(Float, nullable=False)  # in kg
    gender = Column(String(10), nullable=False)  # Male or Female
    vaccines = Column(String(500))
    diseases = Column(String(500))
    medical_history = Column(String(1000))
    personality = Column(String(500))
    created_at = Column(DateTime, default=datetime.utcnow)

def get_latest_timestamp(session, model):
    """Get the latest timestamp from a model's records"""
    latest = session.query(model).order_by(model.created_at.desc()).first()
    return latest.created_at if latest else datetime.min

def sync_databases():
    # Create both database engines
    sqlite_engine = create_engine('sqlite:///adoptease.db')
    postgres_engine = create_engine(os.getenv('DATABASE_URL'))
    
    # Create sessions
    SQLiteSession = sessionmaker(bind=sqlite_engine)
    PostgreSQLSession = sessionmaker(bind=postgres_engine)
    sqlite_session = SQLiteSession()
    postgres_session = PostgreSQLSession()

    try:
        # Get latest timestamps from both databases
        sqlite_latest_user = get_latest_timestamp(sqlite_session, User)
        sqlite_latest_dog = get_latest_timestamp(sqlite_session, Dog)
        postgres_latest_user = get_latest_timestamp(postgres_session, User)
        postgres_latest_dog = get_latest_timestamp(postgres_session, Dog)

        # Forward sync (SQLite to PostgreSQL)
        if sqlite_latest_user > postgres_latest_user:
            print("Syncing users from SQLite to PostgreSQL...")
            users = sqlite_session.query(User).all()
            for user in users:
                existing = postgres_session.query(User).filter_by(email=user.email).first()
                if not existing:
                    new_user = User(
                        name=user.name,
                        email=user.email,
                        password=user.password,
                        type=user.type,
                        created_at=user.created_at
                    )
                    postgres_session.add(new_user)

        if sqlite_latest_dog > postgres_latest_dog:
            print("Syncing dogs from SQLite to PostgreSQL...")
            dogs = sqlite_session.query(Dog).all()
            for dog in dogs:
                existing = postgres_session.query(Dog).filter_by(
                    name=dog.name,
                    breed=dog.breed,
                    created_at=dog.created_at
                ).first()
                if not existing:
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

        # Reverse sync (PostgreSQL to SQLite)
        if postgres_latest_user > sqlite_latest_user:
            print("Syncing users from PostgreSQL to SQLite...")
            users = postgres_session.query(User).all()
            for user in users:
                existing = sqlite_session.query(User).filter_by(email=user.email).first()
                if not existing:
                    new_user = User(
                        name=user.name,
                        email=user.email,
                        password=user.password,
                        type=user.type,
                        created_at=user.created_at
                    )
                    sqlite_session.add(new_user)

        if postgres_latest_dog > sqlite_latest_dog:
            print("Syncing dogs from PostgreSQL to SQLite...")
            dogs = postgres_session.query(Dog).all()
            for dog in dogs:
                existing = sqlite_session.query(Dog).filter_by(
                    name=dog.name,
                    breed=dog.breed,
                    created_at=dog.created_at
                ).first()
                if not existing:
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
                    sqlite_session.add(new_dog)

        # Commit changes to both databases
        postgres_session.commit()
        sqlite_session.commit()
        print("Database synchronization completed successfully!")

    except Exception as e:
        print(f"Error during synchronization: {str(e)}")
        postgres_session.rollback()
        sqlite_session.rollback()
        raise

    finally:
        postgres_session.close()
        sqlite_session.close()

if __name__ == "__main__":
    sync_databases() 