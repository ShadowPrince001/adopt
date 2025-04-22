import os
from dotenv import load_dotenv
from sync_databases import sync_databases, db
from flask import Flask

def main():
    load_dotenv()
    
    # Create Flask app
    app = Flask(__name__)
    if os.getenv("DATABASE_URL"):
        app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL").replace("postgres://", "postgresql://")
    else:
        app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///adoptease.db"
    
    # Initialize Flask-SQLAlchemy
    db.init_app(app)
    
    # Create tables if they don't exist
    with app.app_context():
        db.create_all()
        sync_databases()

if __name__ == "__main__":
    main() 