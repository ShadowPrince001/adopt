from flask import Flask, request, jsonify, send_from_directory
import os
import jwt
import requests
import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
load_dotenv()
app = Flask(__name__, static_folder='.')
app.config['SECRET_KEY'] = 'adopt_ease_secret_key'  
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///adoptease.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(50), nullable=False)
    name = db.Column(db.String(50), nullable=False)
    type = db.Column(db.String(50), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    
    def __repr__(self):
        return f'<User {self.email}>'


with app.app_context():
    db.create_all()
    
    admin = User.query.filter_by(type='admin').first()
    if not admin:
        admin_user = User(
            email='maheeyan@gmail.com',
            password=generate_password_hash('admin123'),
            name='Maheeyan Saha',
            type='admin'
        )
        db.session.add(admin_user)
        db.session.commit()
        print('Admin user created successfully')

class Dog(db.Model):
    __tablename__ = 'dogs'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    breed = db.Column(db.String(100), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    vaccines = db.Column(db.String(200), nullable=True)
    diseases = db.Column(db.String(200), nullable=True)
    medical_history = db.Column(db.String(500), nullable=True)
    personality = db.Column(db.String(200), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    def __repr__(self):
        return f'<Dog {self.name}, {self.breed}>'




@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('.', path)

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    
    if not data:
        return jsonify({'message': 'Invalid request data'}), 400
    
    email = data.get('email', '')
    password = data.get('password', '')
    remember_me = data.get('rememberMe', False)
    
    
    user = User.query.filter_by(email=email).first()
    
    if not user:
        return jsonify({'message': 'User not found'}), 401
    
    if not check_password_hash(user.password, password):
        return jsonify({'message': 'Incorrect password'}), 401
    
    
    expiration = datetime.datetime.utcnow() + datetime.timedelta(days=30 if remember_me else 1)
    token = jwt.encode(
        {
            'email': user.email,
            'name': user.name,
            'exp': expiration,
            'role': user.type
        },
        app.config['SECRET_KEY']
    )
    
    
    if isinstance(token, bytes):
        token = token.decode('utf-8')

    return jsonify({
        'message': 'Login successful',
        'token': token,
        'name': user.name,
        'type': user.type
    })

@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    
    if not data:
        return jsonify({'message': 'Invalid request data'}), 400
    
    email = data.get('email', '')
    password = data.get('password', '')
    name = data.get('name', '')
    type = data.get('type', '')     

    
    if not email or not password or not name or not type:
        return jsonify({'message': 'All fields are required'}), 400
    
    
    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        return jsonify({'message': 'User already exists'}), 409
    
    
    hashed_password = generate_password_hash(password)
    new_user = User(email=email, password=hashed_password, name=name, type=type)
    
    try:
        db.session.add(new_user)
        db.session.commit()
        return jsonify({'message': 'Registration successful', 'type': type})
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Registration failed: {str(e)}'}), 500

@app.route('/api/verify-token', methods=['GET'])
def verify_token():
    auth_header = request.headers.get('Authorization')
    
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({'message': 'Authorization header missing or invalid'}), 401
    
    token = auth_header.split(' ')[1]
    
    try:
        payload = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        
        user = User.query.filter_by(email=payload['email']).first()
        if not user:
            return jsonify({'message': 'User no longer exists'}), 401
        
        return jsonify({
            'valid': True,
            'user': {
                'email': user.email,
                'name': user.name,
                'type': user.type
            }
        })
    except jwt.ExpiredSignatureError:
        return jsonify({'message': 'Token expired'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'message': 'Invalid token'}), 401


@app.route('/api/admin/users', methods=['GET'])
def get_all_users():
   
    auth_header = request.headers.get('Authorization')
    
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({'message': 'Authorization header missing or invalid'}), 401
    
    token = auth_header.split(' ')[1]
    
    try:
        
        payload = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        
        
        if payload['role'] != 'admin':
            return jsonify({'message': 'Unauthorized access'}), 403
        
        
        users = User.query.all()
        user_list = []
        
        for user in users:
            user_data = {
                'id': user.id,
                'email': user.email,
                'name': user.name,
                'type': user.type,
                'created_at': user.created_at
            }
            user_list.append(user_data)
            
        return jsonify({'users': user_list})
    except jwt.ExpiredSignatureError:
        return jsonify({'message': 'Token expired'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'message': 'Invalid token'}), 401





    
@app.route('/api/admin/dogs', methods=['POST'])
def add_dog():
    data = request.get_json()
    if not data:
        return jsonify({'message': 'Invalid data'}), 400

    try:
        new_dog = Dog(
            name=data.get('name'),
            breed=data.get('breed'),
            age=data.get('age'),
            vaccines=data.get('vaccines'),
            diseases=data.get('diseases'),
            medical_history=data.get('medical_history'),
            personality=data.get('personality')
        )
        db.session.add(new_dog)
        db.session.commit()
        return jsonify({'message': 'Dog added successfully'}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Error adding dog: {str(e)}'}), 500
    
@app.route('/api/admin/dogs/<int:dog_id>', methods=['PUT'])
def edit_dog(dog_id):
    data = request.get_json()
    dog = Dog.query.get(dog_id)
    if not dog:
        return jsonify({'message': 'Dog not found'}), 404

    try:
        dog.name = data.get('name', dog.name)
        dog.breed = data.get('breed', dog.breed)
        dog.age = data.get('age', dog.age)
        dog.vaccines = data.get('vaccines', dog.vaccines)
        dog.diseases = data.get('diseases', dog.diseases)
        dog.medical_history = data.get('medical_history', dog.medical_history)
        dog.personality = data.get('personality', dog.personality)

        db.session.commit()
        return jsonify({'message': 'Dog updated successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Error updating dog: {str(e)}'}), 500

@app.route('/api/admin/dogs/<int:dog_id>', methods=['DELETE'])
def delete_dog(dog_id):
    dog = Dog.query.get(dog_id)
    if not dog:
        return jsonify({'message': 'Dog not found'}), 404

    try:
        db.session.delete(dog)
        db.session.commit()
        return jsonify({'message': 'Dog deleted successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Error deleting dog: {str(e)}'}), 500

@app.route('/api/expert/dogs', methods=['GET'])
def get_dogs():
    
    
    
        dogs = Dog.query.all()
        dog_list = [
            {
                'id': dog.id,
                'name': dog.name,
                'breed': dog.breed,
                'age': dog.age,
                'vaccines': dog.vaccines,
                'diseases': dog.diseases,
                'medical_history': dog.medical_history,
                'personality': dog.personality
            } for dog in dogs
        ]
        return jsonify({'dogs': dog_list})
    
def get_customer_view_dogs():
    
    dogs = Dog.query.all()
    return [
        {
            'id': dog.id,
            'breed': dog.breed,
            'name': dog.name,
            'age': dog.age,
            'personality': dog.personality,
            'created_at': dog.created_at
        } for dog in dogs
    ]
@app.route('/api/customer/dogs', methods=['GET'])
def get_all_dog():
    # (auth checks...)
    try:
        dog_list = get_customer_view_dogs()
        return jsonify({'dogs': dog_list})
    except:
        return jsonify({'dogs': []}), 500

@app.route('/chat', methods=['POST'])
def chat():
    user_msg = request.json.get('message', '')

    dog_info = get_all_dog()
    if isinstance(dog_info, tuple):
        dog_data = dog_info[0].get_json().get('dogs', [])
    else:
        dog_data = dog_info.get_json().get('dogs', [])

    custom_prompt = (
        "You are a helpful AI assistant on a pet adoption website (AdoptEase). "
        "Only answer using the given dog data and avoid medical advice.\n"
        f"Here is the list of dogs:\n{dog_data}\n"
    )

    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": custom_prompt},
            {"role": "user", "content": user_msg}
        ]
    }

    headers = {
        "Authorization": f"Bearer {os.getenv('DEEPSEEK_API_KEY')}",  # uses .env value
        "Content-Type": "application/json"
    }

    res = requests.post("https://api.deepseek.com/v1/chat/completions", json=payload, headers=headers)

    try:
        if res.status_code == 402:  # Insufficient balance error
            return jsonify({"reply": "Sorry, our AI service is currently unavailable due to insufficient balance. Please try again later."}), 402
        
        print("Status:", res.status_code)
        print("Response:", res.text)

        reply = res.json()["choices"][0]["message"]["content"]
    except (KeyError, IndexError):
        reply = "Sorry, something went wrong with the AI response."

    return jsonify({"reply": reply})

   
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True) 