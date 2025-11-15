# backend/utils/security.py
import os
from functools import wraps
from flask import request, jsonify
import jwt
import bcrypt

# --- Secret Key ---
SECRET_KEY = os.getenv('SECRET_KEY', 'default-secret-key')

def hash_password(password):
    """Hash a password using bcrypt."""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password, hashed_password):
    """Verify a password against a hashed password using bcrypt."""
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))

def encode_auth_token(user_id, role):
    """Generate a JWT token for authentication."""
    try:
        payload = {'user_id': user_id, 'role': role}
        return jwt.encode(payload, SECRET_KEY, algorithm='HS256')
    except Exception as e:
        return str(e)

# --- Authentication Decorator ---
def token_required(f):
    """Decorator to require a valid JWT token."""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token or not token.startswith('Bearer '):
            return jsonify({'message': 'Token is missing or invalid!'}), 401
        
        token = token.split(' ')[1]
        
        try:
            # Decode token and attach user info to request
            data = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            request.user_id = data['user_id']
            request.user_role = data['role']
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token has expired!'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Token is invalid!'}), 401
            
        return f(*args, **kwargs)
    return decorated

def admin_required(f):
    """Decorator to require admin role."""
    @wraps(f)
    @token_required
    def decorated(*args, **kwargs):
        if request.user_role != 'admin':
            return jsonify({'message': 'Admin access required!'}), 403
        return f(*args, **kwargs)
    return decorated