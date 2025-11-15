# backend/routes/auth_routes.py
import os
import mysql.connector
from flask import Blueprint, request, jsonify
from config.db_connector import db
from utils.security import hash_password, verify_password, encode_auth_token

auth_bp = Blueprint('auth_bp', __name__)

@auth_bp.route('/signup', methods=['POST'])
def signup():
    data = request.json
    name, email, password, role = data.get('name'), data.get('email'), data.get('password'), data.get('role', 'student')
    if not all([name, email, password]):
        return jsonify({"error": "Missing fields"}), 400

    password_hash = hash_password(password)
    cursor = db.get_cursor()

    try:
        query = "INSERT INTO Users (name, email, password_hash, role) VALUES (%s, %s, %s, %s)"
        cursor.execute(query, (name, email, password_hash, role))
        db.conn.commit()
        return jsonify({"message": "User registered successfully!"}), 201
    except mysql.connector.Error as err:
        return jsonify({"error": f"Email might exist. {err}"}), 409
    finally:
        cursor.close()

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.json
    email, password = data.get('email'), data.get('password')
    cursor = db.get_cursor(dictionary=True)
    cursor.execute("SELECT user_id, password_hash, role FROM Users WHERE email = %s", (email,))
    user = cursor.fetchone()
    cursor.close()

    if user and verify_password(password, user['password_hash']):
        token = encode_auth_token(user['user_id'], user['role'])
        return jsonify({"message": "Login successful", "token": token, "role": user['role'], "user_id": user['user_id']}), 200

    return jsonify({"error": "Invalid email or password"}), 401
