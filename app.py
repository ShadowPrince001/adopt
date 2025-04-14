from flask import Flask, request, jsonify, send_from_directory
import os
import jwt
import requests
import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__, static_folder=".")
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "default_secret_key_for_development_only")
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///adoptease.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Print environment variables for debugging
print("Environment variables loaded:")
print(f"SECRET_KEY: {'Set' if os.getenv('SECRET_KEY') else 'Not set'}")
print(f"OPENROUTER_API_KEY: {'Set' if os.getenv('OPENROUTER_API_KEY') else 'Not set'}")

db = SQLAlchemy(app)

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

    return jsonify(
        {
            "message": "Login successful",
            "token": token,
            "name": user.name,
            "type": user.type,
        }
    )


@app.route("/api/register", methods=["POST"])
def register():
    data = request.get_json()

    if not data:
        return jsonify({"message": "Invalid request data"}), 400

    email = data.get("email", "")
    password = data.get("password", "")
    name = data.get("name", "")
    type = data.get("type", "")

    if not email or not password or not name or not type:
        return jsonify({"message": "All fields are required"}), 400

    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        return jsonify({"message": "User already exists"}), 409

    hashed_password = generate_password_hash(password)
    new_user = User(email=email, password=hashed_password, name=name, type=type)

    try:
        db.session.add(new_user)
        db.session.commit()
        return jsonify({"message": "Registration successful", "type": type})
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": f"Registration failed: {str(e)}"}), 500


@app.route("/api/verify-token", methods=["GET"])
def verify_token():
    auth_header = request.headers.get("Authorization")

    if not auth_header or not auth_header.startswith("Bearer "):
        return jsonify({"message": "Authorization header missing or invalid"}), 401

    token = auth_header.split(" ")[1]

    try:
        payload = jwt.decode(token, app.config["SECRET_KEY"], algorithms=["HS256"])

        user = User.query.filter_by(email=payload["email"]).first()
        if not user:
            return jsonify({"message": "User no longer exists"}), 401

        return jsonify(
            {
                "valid": True,
                "user": {"email": user.email, "name": user.name, "type": user.type},
            }
        )
    except jwt.ExpiredSignatureError:
        return jsonify({"message": "Token expired"}), 401
    except jwt.InvalidTokenError:
        return jsonify({"message": "Invalid token"}), 401


@app.route("/api/admin/users", methods=["GET"])
def get_all_users():

    auth_header = request.headers.get("Authorization")

    if not auth_header or not auth_header.startswith("Bearer "):
        return jsonify({"message": "Authorization header missing or invalid"}), 401

    token = auth_header.split(" ")[1]

    try:

        payload = jwt.decode(token, app.config["SECRET_KEY"], algorithms=["HS256"])

        if payload["role"] != "admin":
            return jsonify({"message": "Unauthorized access"}), 403

        users = User.query.all()
        user_list = []

        for user in users:
            user_data = {
                "id": user.id,
                "email": user.email,
                "name": user.name,
                "type": user.type,
                "created_at": user.created_at,
            }
            user_list.append(user_data)

        return jsonify({"users": user_list})
    except jwt.ExpiredSignatureError:
        return jsonify({"message": "Token expired"}), 401
    except jwt.InvalidTokenError:
        return jsonify({"message": "Invalid token"}), 401


@app.route("/api/admin/dogs", methods=["GET"])
def get_admin_dogs():
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return jsonify({"message": "Authorization header missing or invalid"}), 401

    token = auth_header.split(" ")[1]

    try:
        payload = jwt.decode(token, app.config["SECRET_KEY"], algorithms=["HS256"])
        if payload["role"] != "admin":
            return jsonify({"message": "Unauthorized access"}), 403

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
    except jwt.ExpiredSignatureError:
        return jsonify({"message": "Token expired"}), 401
    except jwt.InvalidTokenError:
        return jsonify({"message": "Invalid token"}), 401
    except Exception as e:
        return jsonify({"message": f"Error loading dogs: {str(e)}"}), 500


@app.route("/api/admin/dogs", methods=["POST"])
def add_dog():
    data = request.get_json()
    if not data:
        return jsonify({"message": "Invalid data"}), 400

    try:
        # Validate age
        age = int(data.get("age", 0))
        if age < 0 or age > 35:  # Updated age range (0-35 years)
            return jsonify({"message": "Age must be between 0 and 35 years"}), 400

        # Validate height and weight
        height = float(data.get("height", 0))
        weight = float(data.get("weight", 0))
        
        if height < 7.5 or height > 150:  # Updated height range (7.5cm to 1.5m)
            return jsonify({"message": "Height must be between 7.5cm and 150cm"}), 400
        if weight < 0.25 or weight > 200:  # Updated weight range (0.25kg to 200kg)
            return jsonify({"message": "Weight must be between 0.25kg and 200kg"}), 400

        new_dog = Dog(
            name=data.get("name"),
            breed=data.get("breed"),
            age=age,
            color=data.get("color"),
            height=height,
            weight=weight,
            vaccines=data.get("vaccines"),
            diseases=data.get("diseases"),
            medical_history=data.get("medical_history"),
            personality=data.get("personality"),
        )
        db.session.add(new_dog)
        db.session.commit()
        return jsonify({"message": "Dog added successfully"}), 201
    except ValueError as e:
        return jsonify({"message": "Age, height, and weight must be valid numbers"}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": f"Error adding dog: {str(e)}"}), 500


@app.route("/api/admin/dogs/<int:dog_id>", methods=["PUT"])
def edit_dog(dog_id):
    data = request.get_json()
    dog = Dog.query.get(dog_id)
    if not dog:
        return jsonify({"message": "Dog not found"}), 404

    try:
        # Validate age if it's being updated
        if "age" in data:
            age = int(data["age"])
            if age < 0 or age > 35:  # Updated age range (0-35 years)
                return jsonify({"message": "Age must be between 0 and 35 years"}), 400
            dog.age = age
            
        # Validate height and weight if they are being updated
        if "height" in data:
            height = float(data["height"])
            if height < 7.5 or height > 150:  # Updated height range (7.5cm to 1.5m)
                return jsonify({"message": "Height must be between 7.5cm and 150cm"}), 400
            dog.height = height
            
        if "weight" in data:
            weight = float(data["weight"])
            if weight < 0.25 or weight > 200:  # Updated weight range (0.25kg to 200kg)
                return jsonify({"message": "Weight must be between 0.25kg and 200kg"}), 400
            dog.weight = weight

        dog.name = data.get("name", dog.name)
        dog.breed = data.get("breed", dog.breed)
        dog.color = data.get("color", dog.color)
        dog.vaccines = data.get("vaccines", dog.vaccines)
        dog.diseases = data.get("diseases", dog.diseases)
        dog.medical_history = data.get("medical_history", dog.medical_history)
        dog.personality = data.get("personality", dog.personality)

        db.session.commit()
        return jsonify({"message": "Dog updated successfully"}), 200
    except ValueError as e:
        return jsonify({"message": "Age, height, and weight must be valid numbers"}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": f"Error updating dog: {str(e)}"}), 500


@app.route("/api/admin/dogs/<int:dog_id>", methods=["DELETE"])
def delete_dog(dog_id):
    dog = Dog.query.get(dog_id)
    if not dog:
        return jsonify({"message": "Dog not found"}), 404

    try:
        db.session.delete(dog)
        db.session.commit()
        return jsonify({"message": "Dog deleted successfully"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": f"Error deleting dog: {str(e)}"}), 500


@app.route("/api/expert/dogs", methods=["GET"])
def get_dogs():
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
        }
        for dog in dogs
    ]
    return jsonify({"dogs": dog_list})


def get_customer_view_dogs():
    dogs = Dog.query.all()
    return [
        {
            "id": dog.id,
            "breed": dog.breed,
            "name": dog.name,
            "age": dog.age,
            "color": dog.color,
            "height": dog.height,
            "weight": dog.weight,
            "vaccines": dog.vaccines,
            "diseases": dog.diseases,
            "medical_history": dog.medical_history,
            "personality": dog.personality,
            "created_at": dog.created_at,
        }
        for dog in dogs
    ]


@app.route("/api/customer/dogs", methods=["GET"])
def get_all_dog():
    # (auth checks...)
    try:
        dog_list = get_customer_view_dogs()
        return jsonify({"dogs": dog_list})
    except:
        return jsonify({"dogs": []}), 500


@app.route("/chat", methods=["POST"])
def chat():
    try:
        # Check if user is authenticated
        token = request.headers.get('Authorization')
        if not token or not token.startswith('Bearer '):
            print("Auth error: No token or invalid token format")
            return jsonify({"error": "Unauthorized access"}), 401

        user_msg = request.json.get("message", "")
        if not user_msg:
            print("Error: No message provided")
            return jsonify({"error": "Message is required"}), 400

        # Get OpenRouter API key from environment
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            print("Error: OpenRouter API key not found in environment variables")
            return jsonify({"error": "OpenRouter API key not configured"}), 500

        print(f"Making request to OpenRouter with message: {user_msg}")

        # Make request to OpenRouter
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
                "HTTP-Referer": request.host_url,
                "X-Title": "AdoptEase"
            },
            json={
                "model": "openai/gpt-3.5-turbo",
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a helpful AI assistant on a pet adoption website (AdoptEase). You help users with questions about dogs, adoption process, and pet care. Be friendly, informative, and concise."
                    },
                    {
                        "role": "user",
                        "content": user_msg
                    }
                ]
            }
        )

        print(f"OpenRouter response status: {response.status_code}")
        print(f"OpenRouter response: {response.text}")

        if response.status_code != 200:
            error_msg = f"OpenRouter API error: {response.status_code} - {response.text}"
            print(error_msg)
            return jsonify({"error": "Failed to get response from AI service"}), 500

        data = response.json()
        return jsonify({"response": data["choices"][0]["message"]["content"]})

    except requests.exceptions.RequestException as e:
        print(f"Network error: {str(e)}")
        return jsonify({"error": "Network error occurred while contacting AI service"}), 500
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        return jsonify({"error": "An unexpected error occurred"}), 500


@app.route("/api/expert/dogs/<int:dog_id>", methods=["PUT"])
def update_expert_dog(dog_id):
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return jsonify({"message": "Authorization header missing or invalid"}), 401

    token = auth_header.split(" ")[1]

    try:
        payload = jwt.decode(token, app.config["SECRET_KEY"], algorithms=["HS256"])
        if payload["role"] != "expert":
            return jsonify({"message": "Unauthorized access"}), 403

        data = request.get_json()
        dog = Dog.query.get(dog_id)
        if not dog:
            return jsonify({"message": "Dog not found"}), 404

        # Experts can update medical-related fields and physical attributes
        if "vaccines" in data:
            dog.vaccines = data["vaccines"]
        if "diseases" in data:
            dog.diseases = data["diseases"]
        if "medical_history" in data:
            dog.medical_history = data["medical_history"]
        if "personality" in data:
            dog.personality = data["personality"]
        if "color" in data:
            dog.color = data["color"]
        if "height" in data:
            height = float(data["height"])
            if height < 7.5 or height > 150:
                return jsonify({"message": "Height must be between 7.5cm and 150cm"}), 400
            dog.height = height
        if "weight" in data:
            weight = float(data["weight"])
            if weight < 0.25 or weight > 200:
                return jsonify({"message": "Weight must be between 0.25kg and 200kg"}), 400
            dog.weight = weight

        db.session.commit()
        return jsonify({"message": "Dog updated successfully"}), 200
    except ValueError as e:
        return jsonify({"message": "Height and weight must be valid numbers"}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": str(e)}), 500






if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))

    app.run(host="0.0.0.0", port=port, debug=True)
