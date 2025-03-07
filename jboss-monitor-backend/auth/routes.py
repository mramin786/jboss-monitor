# auth/routes.py
from flask import Blueprint, request, jsonify
import os
import json
import uuid
import hashlib
import jwt
from datetime import datetime, timedelta
from functools import wraps

from config import Config

auth_bp = Blueprint('auth', __name__)

def generate_password_hash(password):
    """Create a secure hash of the password"""
    salt = uuid.uuid4().hex
    return hashlib.sha256(salt.encode() + password.encode()).hexdigest() + ':' + salt

def check_password_hash(hashed_password, user_password):
    """Check if the password matches the hash"""
    password, salt = hashed_password.split(':')
    return password == hashlib.sha256(salt.encode() + user_password.encode()).hexdigest()

def get_user_by_username(username):
    """Retrieve user data from file storage"""
    user_file = os.path.join(Config.USERS_PATH, f"{username}.json")
    if os.path.exists(user_file):
        with open(user_file, 'r') as f:
            return json.load(f)
    return None

def save_user(user_data):
    """Save user data to file storage"""
    user_file = os.path.join(Config.USERS_PATH, f"{user_data['username']}.json")
    with open(user_file, 'w') as f:
        json.dump(user_data, f)

def token_required(f):
    """Decorator to check for valid JWT token"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'Authorization' in request.headers:
            token = request.headers['Authorization'].split(" ")[1]
        
        if not token:
            return jsonify({'message': 'Token is missing'}), 401
        
        try:
            data = jwt.decode(token, Config.JWT_SECRET_KEY, algorithms=["HS256"])
            current_user = get_user_by_username(data['username'])
            if not current_user:
                return jsonify({'message': 'User not found'}), 401
        except:
            return jsonify({'message': 'Token is invalid'}), 401
            
        return f(current_user, *args, **kwargs)
    
    return decorated

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({'message': 'Missing required fields'}), 400
    
    # Check if user already exists
    if get_user_by_username(data['username']):
        return jsonify({'message': 'User already exists'}), 409
    
    # Create new user
    user = {
        'username': data['username'],
        'password': generate_password_hash(data['password']),
        'role': data.get('role', 'user'),
        'created_at': datetime.now().isoformat()
    }
    
    save_user(user)
    
    return jsonify({'message': 'User registered successfully'}), 201

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({'message': 'Missing required fields'}), 400
    
    user = get_user_by_username(data['username'])
    
    if not user or not check_password_hash(user['password'], data['password']):
        return jsonify({'message': 'Invalid credentials'}), 401
    
    # Generate JWT token
    token = jwt.encode({
        'username': user['username'],
        'role': user['role'],
        'exp': datetime.utcnow() + Config.JWT_ACCESS_TOKEN_EXPIRES
    }, Config.JWT_SECRET_KEY)
    
    return jsonify({
        'token': token,
        'username': user['username'],
        'role': user['role'],
        'expires': (datetime.utcnow() + Config.JWT_ACCESS_TOKEN_EXPIRES).isoformat()
    }), 200

@auth_bp.route('/jboss-credentials', methods=['POST'])
@token_required
def store_jboss_credentials(current_user):
    data = request.get_json()
    
    if not data or not data.get('environment') or not data.get('username') or not data.get('password'):
        return jsonify({'message': 'Missing required fields'}), 400
    
    # Store JBoss credentials for the environment
    env = data['environment']
    
    # Update user with JBoss credentials
    current_user[f'{env}_jboss_username'] = data['username']
    current_user[f'{env}_jboss_password'] = data['password']  # In a real app, encrypt this
    
    save_user(current_user)
    
    return jsonify({'message': 'JBoss credentials stored successfully'}), 200

@auth_bp.route('/profile', methods=['GET'])
@token_required
def get_profile(current_user):
    # Return user profile without sensitive data
    profile = {
        'username': current_user['username'],
        'role': current_user['role'],
        'created_at': current_user['created_at'],
        'has_prod_credentials': 'production_jboss_username' in current_user,
        'has_nonprod_credentials': 'non_production_jboss_username' in current_user
    }
    
    return jsonify(profile), 200
