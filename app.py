from flask import Flask, request, jsonify, send_from_directory
import os
import jwt
import requests
import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
import logging
from functools import wraps

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()
app = Flask(__name__, static_folder=".")
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "default_secret_key_for_development_only")
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///adoptease.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["RATE_LIMIT"] = "100 per day"  # Basic rate limiting

# Print environment variables for debugging
logger.info("Environment variables loaded:")
logger.info(f"SECRET_KEY: {'Set' if os.getenv('SECRET_KEY') else 'Not set'}")
logger.info(f"OPENROUTER_API_KEY: {'Set' if os.getenv('OPENROUTER_API_KEY') else 'Not set'}")

db = SQLAlchemy(app)

# Error handling middleware
@app.errorhandler(Exception)
def handle_error(error):
    logger.error(f"Error occurred: {str(error)}")
    return jsonify({"message": "An internal server error occurred"}), 500

# Authentication decorator
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return jsonify({"message": "Authorization header missing or invalid"}), 401

        token = auth_header.split(" ")[1]
        try:
            payload = jwt.decode(token, app.config["SECRET_KEY"], algorithms=["HS256"])
            user = User.query.filter_by(email=payload["email"]).first()
            if not user:
                return jsonify({"message": "User no longer exists"}), 401
            return f(user, *args, **kwargs)
        except jwt.ExpiredSignatureError:
            return jsonify({"message": "Token expired"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"message": "Invalid token"}), 401
    return decorated

# Admin role check decorator
def admin_required(f):
    @wraps(f)
    def decorated(user, *args, **kwargs):
        if user.type != "admin":
            return jsonify({"message": "Unauthorized access"}), 403
        return f(user, *args, **kwargs)
    return decorated

# Define models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    type = db.Column(db.String(20), nullable=False)  # admin, customer, or expert
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

class Dog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    breed = db.Column(db.String(100), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    color = db.Column(db.String(100), nullable=False)
    height = db.Column(db.Float, nullable=False)  # in cm
    weight = db.Column(db.Float, nullable=False)  # in kg
    vaccines = db.Column(db.String(500))
    diseases = db.Column(db.String(500))
    medical_history = db.Column(db.String(1000))
    personality = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

# Input validation functions
def validate_dog_data(data):
    errors = []
    if not data.get('name') or len(data['name']) < 2:
        errors.append("Name must be at least 2 characters long")
    if not data.get('breed') or len(data['breed']) < 2:
        errors.append("Breed must be at least 2 characters long")
    if not data.get('age') or not isinstance(data['age'], int) or data['age'] < 0 or data['age'] > 30:
        errors.append("Age must be a positive number between 0 and 30")
    if not data.get('color') or len(data['color']) < 2:
        errors.append("Color must be at least 2 characters long")
    if not data.get('height') or not isinstance(data['height'], (int, float)) or data['height'] <= 0 or data['height'] > 200:
        errors.append("Height must be a positive number between 0 and 200 cm")
    if not data.get('weight') or not isinstance(data['weight'], (int, float)) or data['weight'] <= 0 or data['weight'] > 100:
        errors.append("Weight must be a positive number between 0 and 100 kg")
    return errors

def validate_user_data(data):
    errors = []
    if not data.get('name') or len(data['name']) < 2:
        errors.append("Name must be at least 2 characters long")
    if not data.get('email') or not '@' in data['email']:
        errors.append("Invalid email format")
    if not data.get('password') or len(data['password']) < 8:
        errors.append("Password must be at least 8 characters long")
    if not data.get('type') or data['type'] not in ['admin', 'customer', 'expert']:
        errors.append("Invalid user type")
    return errors

# Create tables
with app.app_context():
    db.create_all()
    
    # Create admin user if it doesn't exist
    admin = User.query.filter_by(type='admin').first()
    if not admin:
        admin = User(
            name='Maheeyan',
            email='maheeyan@gmail.com',
            password=generate_password_hash('admin123'),
            type='admin'
        )
        db.session.add(admin)
        db.session.commit()

@app.route("/")
def index():
    return send_from_directory(".", "index.html")

@app.route("/<path:path>")
def serve_static(path):
    return send_from_directory(".", path)

@app.route("/api/login", methods=["POST"])
def login():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"message": "Invalid request data"}), 400

        email = data.get("email", "")
        password = data.get("password", "")
        remember_me = data.get("rememberMe", False)

        user = User.query.filter_by(email=email).first()
        if not user:
            return jsonify({"message": "User not found"}), 401

        if not check_password_hash(user.password, password):
            return jsonify({"message": "Incorrect password"}), 401

        expiration = datetime.datetime.utcnow() + datetime.timedelta(
            days=30 if remember_me else 1
        )
        token = jwt.encode(
            {"email": user.email, "name": user.name, "exp": expiration, "role": user.type},
            app.config["SECRET_KEY"],
            algorithm="HS256"
        )

        logger.info(f"User {email} logged in successfully")
        return jsonify({
            "message": "Login successful",
            "token": token,
            "name": user.name,
            "type": user.type,
        })
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        return jsonify({"message": "An error occurred during login"}), 500

@app.route("/api/register", methods=["POST"])
def register():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"message": "Invalid request data"}), 400

        errors = validate_user_data(data)
        if errors:
            return jsonify({"message": "Validation failed", "errors": errors}), 400

        existing_user = User.query.filter_by(email=data['email']).first()
        if existing_user:
            return jsonify({"message": "User already exists"}), 409

        hashed_password = generate_password_hash(data['password'])
        new_user = User(
            email=data['email'],
            password=hashed_password,
            name=data['name'],
            type=data['type']
        )

        db.session.add(new_user)
        db.session.commit()
        logger.info(f"New user registered: {data['email']}")
        return jsonify({"message": "Registration successful", "type": data['type']})
    except Exception as e:
        db.session.rollback()
        logger.error(f"Registration error: {str(e)}")
        return jsonify({"message": "An error occurred during registration"}), 500

@app.route("/api/verify-token", methods=["GET"])
@token_required
def verify_token(user):
    return jsonify({
        "valid": True,
        "user": {"email": user.email, "name": user.name, "type": user.type},
    })

@app.route("/api/admin/users", methods=["GET"])
@token_required
@admin_required
def get_all_users(user):
    try:
        users = User.query.all()
        user_list = [
            {
                "id": u.id,
                "email": u.email,
                "name": u.name,
                "type": u.type,
                "created_at": u.created_at,
            }
            for u in users
        ]
        return jsonify({"users": user_list})
    except Exception as e:
        logger.error(f"Error fetching users: {str(e)}")
        return jsonify({"message": "An error occurred while fetching users"}), 500

@app.route("/api/admin/dogs", methods=["GET"])
@token_required
@admin_required
def get_admin_dogs(user):
    try:
        dogs = Dog.query.all()
        dog_list = [
            {
                "id": dog.id,
                "name": dog.name,
                "breed": dog.breed,
                "age": dog.age,
                "color": dog.color,
                "height": dog.height,
                "weight": dog.weight,
                "vaccines": dog.vaccines,
                "diseases": dog.diseases,
                "medical_history": dog.medical_history,
                "personality": dog.personality,
                "created_at": dog.created_at
            }
            for dog in dogs
        ]
        return jsonify({"dogs": dog_list})
    except Exception as e:
        logger.error(f"Error fetching dogs: {str(e)}")
        return jsonify({"message": "An error occurred while fetching dogs"}), 500

@app.route("/api/admin/dogs", methods=["POST"])
@token_required
@admin_required
def add_dog(user):
    try:
        data = request.get_json()
        if not data:
            return jsonify({"message": "Invalid request data"}), 400

        errors = validate_dog_data(data)
        if errors:
            return jsonify({"message": "Validation failed", "errors": errors}), 400

        new_dog = Dog(
            name=data['name'],
            breed=data['breed'],
            age=data['age'],
            color=data['color'],
            height=data['height'],
            weight=data['weight'],
            vaccines=data.get('vaccines', ''),
            diseases=data.get('diseases', ''),
            medical_history=data.get('medical_history', ''),
            personality=data.get('personality', '')
        )

        db.session.add(new_dog)
        db.session.commit()
        logger.info(f"New dog added: {data['name']}")
        return jsonify({"message": "Dog added successfully", "id": new_dog.id}), 201
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error adding dog: {str(e)}")
        return jsonify({"message": "An error occurred while adding the dog"}), 500

@app.route("/api/admin/dogs/<int:dog_id>", methods=["PUT"])
@token_required
@admin_required
def edit_dog(user, dog_id):
    try:
        data = request.get_json()
        if not data:
            return jsonify({"message": "Invalid request data"}), 400

        errors = validate_dog_data(data)
        if errors:
            return jsonify({"message": "Validation failed", "errors": errors}), 400

        dog = Dog.query.get(dog_id)
        if not dog:
            return jsonify({"message": "Dog not found"}), 404

        dog.name = data['name']
        dog.breed = data['breed']
        dog.age = data['age']
        dog.color = data['color']
        dog.height = data['height']
        dog.weight = data['weight']
        dog.vaccines = data.get('vaccines', dog.vaccines)
        dog.diseases = data.get('diseases', dog.diseases)
        dog.medical_history = data.get('medical_history', dog.medical_history)
        dog.personality = data.get('personality', dog.personality)

        db.session.commit()
        logger.info(f"Dog updated: {dog.name}")
        return jsonify({"message": "Dog updated successfully"})
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating dog: {str(e)}")
        return jsonify({"message": "An error occurred while updating the dog"}), 500

@app.route("/api/admin/dogs/<int:dog_id>", methods=["DELETE"])
@token_required
@admin_required
def delete_dog(user, dog_id):
    try:
        dog = Dog.query.get(dog_id)
        if not dog:
            return jsonify({"message": "Dog not found"}), 404

        db.session.delete(dog)
        db.session.commit()
        logger.info(f"Dog deleted: {dog.name}")
        return jsonify({"message": "Dog deleted successfully"})
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting dog: {str(e)}")
        return jsonify({"message": "An error occurred while deleting the dog"}), 500

@app.route("/api/expert/dogs", methods=["GET"])
@token_required
def get_dogs(user):
    try:
        dogs = Dog.query.all()
        dog_list = [
            {
                "id": dog.id,
                "name": dog.name,
                "breed": dog.breed,
                "age": dog.age,
                "color": dog.color,
                "height": dog.height,
                "weight": dog.weight,
                "vaccines": dog.vaccines,
                "diseases": dog.diseases,
                "medical_history": dog.medical_history,
                "personality": dog.personality,
                "created_at": dog.created_at
            }
            for dog in dogs
        ]
        return jsonify({"dogs": dog_list})
    except Exception as e:
        logger.error(f"Error fetching dogs: {str(e)}")
        return jsonify({"message": "An error occurred while fetching dogs"}), 500

@app.route("/api/customer/dogs", methods=["GET"])
@token_required
def get_all_dog(user):
    try:
        dogs = Dog.query.all()
        dog_list = [
            {
                "id": dog.id,
                "name": dog.name,
                "breed": dog.breed,
                "age": dog.age,
                "color": dog.color,
                "height": dog.height,
                "weight": dog.weight,
                "vaccines": dog.vaccines,
                "diseases": dog.diseases,
                "medical_history": dog.medical_history,
                "personality": dog.personality,
                "created_at": dog.created_at
            }
            for dog in dogs
        ]
        return jsonify({"dogs": dog_list})
    except Exception as e:
        logger.error(f"Error fetching dogs: {str(e)}")
        return jsonify({"message": "An error occurred while fetching dogs"}), 500

@app.route("/chat", methods=["POST"])
@token_required
def chat(user):
    try:
        data = request.get_json()
        if not data or "message" not in data:
            return jsonify({"message": "Invalid request data"}), 400

        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            return jsonify({"message": "OpenRouter API key not configured"}), 500

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": "openai/gpt-3.5-turbo",
            "messages": [
                {
                    "role": "system",
                    "content": "You are a helpful assistant for a pet adoption platform. Provide accurate and helpful information about pet care, adoption processes, and general pet-related queries.",
                },
                {"role": "user", "content": data["message"]},
            ],
        }

        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=payload,
        )

        if response.status_code != 200:
            logger.error(f"OpenRouter API error: {response.text}")
            return jsonify({"message": "Error communicating with AI service"}), 500

        return jsonify({"response": response.json()["choices"][0]["message"]["content"]})
    except Exception as e:
        logger.error(f"Chat error: {str(e)}")
        return jsonify({"message": "An error occurred during chat"}), 500

@app.route("/api/expert/dogs/<int:dog_id>", methods=["PUT"])
@token_required
def update_expert_dog(user, dog_id):
    try:
        data = request.get_json()
        if not data:
            return jsonify({"message": "Invalid request data"}), 400

        dog = Dog.query.get(dog_id)
        if not dog:
            return jsonify({"message": "Dog not found"}), 404

        # Update all fields that are provided
        if 'name' in data:
            dog.name = data['name']
        if 'breed' in data:
            dog.breed = data['breed']
        if 'age' in data:
            dog.age = data['age']
        if 'color' in data:
            dog.color = data['color']
        if 'height' in data:
            dog.height = data['height']
        if 'weight' in data:
            dog.weight = data['weight']
        if 'vaccines' in data:
            dog.vaccines = data['vaccines']
        if 'diseases' in data:
            dog.diseases = data['diseases']
        if 'medical_history' in data:
            dog.medical_history = data['medical_history']
        if 'personality' in data:
            dog.personality = data['personality']

        db.session.commit()
        logger.info(f"Expert updated dog {dog.name}")
        return jsonify({"message": "Dog information updated successfully"})
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating dog: {str(e)}")
        return jsonify({"message": "An error occurred while updating the dog"}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))

    app.run(host="0.0.0.0", port=port, debug=True)
