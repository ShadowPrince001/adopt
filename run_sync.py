import os
from dotenv import load_dotenv
from sync_databases import sync_databases, Base
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

def main():
    load_dotenv()
    
    # Create Flask app and SQLAlchemy instance
    app = Flask(__name__)
    if os.getenv("DATABASE_URL"):
        app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL").replace("postgres://", "postgresql://")
    else:
        app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///adoptease.db"
    
    db = SQLAlchemy(app)
    
    # Create tables if they don't exist
    with app.app_context():
        Base.metadata.create_all(db.engine)
        sync_databases()

if __name__ == "__main__":
    main() 