from flask import Flask, request, jsonify, send_from_directory
import os
import jwt
import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__, static_folder='.')
app.config['SECRET_KEY'] = 'adopt_ease_secret_key'  # In production, use a secure environment variable
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///adoptease.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# User model for database
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    
    def __repr__(self):
        return f'<User {self.email}>'

# Create database tables if they don't exist
with app.app_context():
    db.create_all()
    
    # Add a default admin user if none exists
    admin = User.query.filter_by(email='admin@adoptease.com').first()
    if not admin:
        admin_user = User(
            email='admin@adoptease.com',
            password=generate_password_hash('admin123'),
            name='Admin User'
        )
        db.session.add(admin_user)
        db.session.commit()
        print('Admin user created successfully')

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
    
    # Validate credentials
    user = User.query.filter_by(email=email).first()
    
    if not user:
        return jsonify({'message': 'User not found'}), 401
    
    if not check_password_hash(user.password, password):
        return jsonify({'message': 'Incorrect password'}), 401
    
    # Generate JWT token
    expiration = datetime.datetime.utcnow() + datetime.timedelta(days=30 if remember_me else 1)
    token = jwt.encode(
        {
            'email': user.email,
            'name': user.name,
            'exp': expiration
        },
        app.config['SECRET_KEY']
    )
    
    # In newer versions of PyJWT, token is returned as string
    if isinstance(token, bytes):
        token = token.decode('utf-8')
    
    return jsonify({
        'message': 'Login successful',
        'token': token,
        'name': user.name
    })

@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    
    if not data:
        return jsonify({'message': 'Invalid request data'}), 400
    
    email = data.get('email', '')
    password = data.get('password', '')
    name = data.get('name', '')
    
    # Validate input
    if not email or not password or not name:
        return jsonify({'message': 'All fields are required'}), 400
    
    # Check if user already exists
    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        return jsonify({'message': 'User already exists'}), 409
    
    # Create new user
    hashed_password = generate_password_hash(password)
    new_user = User(email=email, password=hashed_password, name=name)
    
    try:
        db.session.add(new_user)
        db.session.commit()
        return jsonify({'message': 'Registration successful'})
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
        # Check if user still exists in database
        user = User.query.filter_by(email=payload['email']).first()
        if not user:
            return jsonify({'message': 'User no longer exists'}), 401
        
        return jsonify({
            'valid': True,
            'user': {
                'email': user.email,
                'name': user.name
            }
        })
    except jwt.ExpiredSignatureError:
        return jsonify({'message': 'Token expired'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'message': 'Invalid token'}), 401

# Admin route to get all users (for demonstration purposes only)
@app.route('/api/admin/users', methods=['GET'])
def get_all_users():
    # Get authorization token
    auth_header = request.headers.get('Authorization')
    
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({'message': 'Authorization header missing or invalid'}), 401
    
    token = auth_header.split(' ')[1]
    
    try:
        # Decode the token
        payload = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        
        # Check if the user is admin (in a real app, you would have a proper role system)
        if payload['email'] != 'admin@adoptease.com':
            return jsonify({'message': 'Unauthorized access'}), 403
        
        # If authorized, return all users
        users = User.query.all()
        user_list = []
        
        for user in users:
            user_data = {
                'id': user.id,
                'email': user.email,
                'name': user.name,
                'created_at': user.created_at
            }
            user_list.append(user_data)
            
        return jsonify({'users': user_list})
    except jwt.ExpiredSignatureError:
        return jsonify({'message': 'Token expired'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'message': 'Invalid token'}), 401

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True) 