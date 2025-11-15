# backend/models/user_model.py

class User:
    TABLE_NAME = "Users"
    
    # Columns map for easy reference
    COLS = ['user_id', 'name', 'email', 'role', 'password_hash']
    
    # Roles defined in the ENUM in db_connector.py
    ROLES = {
        'STUDENT': 'student',
        'FACULTY': 'faculty',
        'ADMIN': 'admin',
    }