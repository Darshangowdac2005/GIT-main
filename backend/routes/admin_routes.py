# backend/routes/admin_routes.py

from flask import Blueprint, request, jsonify
import mysql.connector
from config.db_connector import db
from utils.security import admin_required
from utils.notification import send_claim_resolved_emails
from models.item_model import Item
from models.claim_model import Claim

admin_bp = Blueprint('admin_bp', __name__)

@admin_bp.route('/claims/pending', methods=['GET'])
@admin_required
def get_pending_claims():
    """Admin dashboard view: lists all pending claims."""
    cursor = db.get_cursor(dictionary=True)
    
    # Complex query to fetch claim details along with item titles and user emails
    query = """
        SELECT
            c.claim_id, c.claimed_at, c.verification_details,
            i.item_id, i.title AS item_title, i.status AS item_status, i.reported_by,
            u_claim.name AS claimant_name, u_claim.email AS claimant_email
        FROM Claims c
        JOIN Items i ON c.item_id = i.item_id
        JOIN Users u_claim ON c.claimant_id = u_claim.user_id
    """
    cursor.execute(query)
    claims = cursor.fetchall()
    cursor.close()
    return jsonify(claims)

@admin_bp.route('/claims/resolve', methods=['POST'])
@admin_required
def resolve_claim():
    """Admin action: approves a claim, marks the item as resolved, and sends emails."""
    admin_id = request.user_id
    data = request.json
    claim_id = data.get('claim_id')
    resolution_type = data.get('resolution_type') # 'approve' or 'reject'

    if not claim_id or resolution_type not in ['approve', 'reject']:
        return jsonify({"error": "Missing claim ID or invalid resolution type."}), 400

    cursor = db.get_cursor(dictionary=True)
    
    try:
        if resolution_type == 'approve':
            # 1. Update Claim Status to APPROVED
            cursor.execute("UPDATE Claims SET claim_status = %s WHERE claim_id = %s", 
                           (Claim.STATUSES['APPROVED'], claim_id))
            
            # 2. Update Item Status to RESOLVED (Crucial for the video's resolved status)
            cursor.execute("SELECT item_id, claimant_id FROM Claims WHERE claim_id = %s", (claim_id,))
            claim_info = cursor.fetchone()
            item_id = claim_info['item_id']
            claimant_id = claim_info['claimant_id']

            cursor.execute("UPDATE Items SET status = %s WHERE item_id = %s", 
                           (Item.STATUSES['RESOLVED'], item_id))
            
            # 3. Fetch item reporter and send notification emails (utility function)
            send_claim_resolved_emails(item_id, claimant_id, admin_id) 
            
            db.conn.commit()
            return jsonify({"message": "Claim approved and resolved successfully. Notifications sent."}), 200

        elif resolution_type == 'reject':
            cursor.execute("UPDATE Claims SET claim_status = %s WHERE claim_id = %s", 
                           (Claim.STATUSES['REJECTED'], claim_id))
            db.conn.commit()
            return jsonify({"message": "Claim rejected."}), 200

    except mysql.connector.Error as err:
        db.conn.rollback()
        return jsonify({"error": f"Database error during resolution: {err}"}), 500
    finally:
        cursor.close()


# -----------------------------
# Categories CRUD (Admin only)
# -----------------------------

@admin_bp.route('/categories', methods=['GET'])
@admin_required
def admin_list_categories():
    cursor = db.get_cursor(dictionary=True)
    cursor.execute("SELECT category_id, name FROM Categories ORDER BY name ASC")
    rows = cursor.fetchall()
    cursor.close()
    return jsonify(rows), 200


@admin_bp.route('/categories', methods=['POST'])
@admin_required
def admin_create_category():
    data = request.json or {}
    name = (data.get('name') or '').strip()
    if not name:
        return jsonify({'error': 'Category name is required.'}), 400
    cursor = db.get_cursor()
    try:
        cursor.execute("INSERT INTO Categories (name) VALUES (%s)", (name,))
        db.conn.commit()
        return jsonify({'message': 'Category created', 'category_id': cursor.lastrowid}), 201
    except mysql.connector.Error as err:
        db.conn.rollback()
        return jsonify({'error': f'Database error: {err}'}), 400
    finally:
        cursor.close()


@admin_bp.route('/categories/<int:category_id>', methods=['PUT'])
@admin_required
def admin_update_category(category_id: int):
    data = request.json or {}
    name = (data.get('name') or '').strip()
    if not name:
        return jsonify({'error': 'Category name is required.'}), 400
    cursor = db.get_cursor()
    try:
        cursor.execute("UPDATE Categories SET name = %s WHERE category_id = %s", (name, category_id))
        if cursor.rowcount == 0:
            db.conn.rollback()
            return jsonify({'error': 'Category not found.'}), 404
        db.conn.commit()
        return jsonify({'message': 'Category updated'}), 200
    except mysql.connector.Error as err:
        db.conn.rollback()
        return jsonify({'error': f'Database error: {err}'}), 400
    finally:
        cursor.close()


@admin_bp.route('/categories/<int:category_id>', methods=['DELETE'])
@admin_required
def admin_delete_category(category_id: int):
    cursor = db.get_cursor()
    try:
        cursor.execute("DELETE FROM Categories WHERE category_id = %s", (category_id,))
        if cursor.rowcount == 0:
            db.conn.rollback()
            return jsonify({'error': 'Category not found.'}), 404
        db.conn.commit()
        return jsonify({'message': 'Category deleted'}), 200
    except mysql.connector.Error as err:
        db.conn.rollback()
        # Likely foreign key constraint
        return jsonify({'error': f'Database error: {err}'}), 400
    finally:
        cursor.close()
