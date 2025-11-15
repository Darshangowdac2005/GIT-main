# backend/server.py

from flask import Flask, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import os

from config.db_connector import create_tables_and_seed
from routes.auth_routes import auth_bp
from routes.item_routes import item_bp
from routes.category_routes import category_bp
from routes.admin_routes import admin_bp

load_dotenv()

app = Flask(__name__)
# Load secret key from .env file
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'default-secret-key') 
CORS(app) 

# Initialize database and tables within app context
with app.app_context():
    create_tables_and_seed()

# Register blueprints
app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(item_bp, url_prefix='/api/items')
app.register_blueprint(category_bp, url_prefix='/api/categories')
app.register_blueprint(admin_bp, url_prefix='/api/admin')

@app.route('/', methods=['GET'])
def home():
    return jsonify({"message": "Back2U Flask API is running!"})

if __name__ == '__main__':
    # Run the server
    app.run(debug=True, port=5000)