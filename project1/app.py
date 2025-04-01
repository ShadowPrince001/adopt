from flask import Flask, request, jsonify, send_from_directory
import os
import jwt
import datetime
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__, static_folder='.')
app.config['SECRET_KEY'] = 'adopt_ease_secret_key'  # In production, use a secure environment variable

# Mock user database (replace with a real database in production)
users_db = {
    'user@example.com': {
        'password': generate_password_hash('password123'),
        'name': 'Demo User'
    }
}

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
    if email not in users_db:
        return jsonify({'message': 'User not found'}), 401
    
    user = users_db[email]
    if not check_password_hash(user['password'], password):
        return jsonify({'message': 'Incorrect password'}), 401
    
    # Generate JWT token
    expiration = datetime.datetime.utcnow() + datetime.timedelta(days=30 if remember_me else 1)
    token = jwt.encode(
        {
            'email': email,
            'name': user['name'],
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
        'name': user['name']
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
    if email in users_db:
        return jsonify({'message': 'User already exists'}), 409
    
    # Add new user
    users_db[email] = {
        'password': generate_password_hash(password),
        'name': name
    }
    
    return jsonify({'message': 'Registration successful'})

@app.route('/api/verify-token', methods=['GET'])
def verify_token():
    auth_header = request.headers.get('Authorization')
    
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({'message': 'Authorization header missing or invalid'}), 401
    
    token = auth_header.split(' ')[1]
    
    try:
        payload = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        return jsonify({
            'valid': True,
            'user': {
                'email': payload['email'],
                'name': payload['name']
            }
        })
    except jwt.ExpiredSignatureError:
        return jsonify({'message': 'Token expired'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'message': 'Invalid token'}), 401

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True) 