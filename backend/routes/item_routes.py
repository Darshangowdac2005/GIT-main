# backend/routes/item_routes.py

import mysql.connector
from flask import Blueprint, request, jsonify
from config.db_connector import db
from utils.security import token_required

item_bp = Blueprint('item_bp', __name__)

@item_bp.route('', methods=['POST'])
@token_required
def report_item():
    user_id = request.user_id
    data = request.json
    title = data.get('title')
    description = data.get('description')
    status = data.get('status')
    category_id = data.get('category_id')

    if not all([user_id, title, status, category_id]):
        return jsonify({"error": "Missing essential item details."}), 400

    cursor = db.get_cursor()
    try:
        query = """
            INSERT INTO Items (reported_by, category_id, title, description, status)
            VALUES (%s, %s, %s, %s, %s)
        """
        cursor.execute(query, (user_id, category_id, title, description, status))
        db.conn.commit()
        return jsonify({"message": "Item reported successfully!", "id": cursor.lastrowid}), 201
    except mysql.connector.Error as err:
        return jsonify({"error": f"Could not submit report. {err}"}), 500
    finally:
        cursor.close()

@item_bp.route('/<int:item_id>/claim', methods=['POST'])
@token_required
def claim_item(item_id):
    user_id = request.user_id
    data = request.json
    verification_details = data.get('verification_details', '').strip()

    if not verification_details:
        return jsonify({"error": "Verification details are required."}), 400

    cursor = db.get_cursor()
    try:
        # Check if item exists and is claimable
        cursor.execute("SELECT status FROM Items WHERE item_id = %s", (item_id,))
        item = cursor.fetchone()
        if not item:
            return jsonify({"error": "Item not found."}), 404
        if item[0] == 'resolved':
            return jsonify({"error": "Item already resolved."}), 400

        # Check if there is already a pending claim for this item by this user
        cursor.execute("""
            SELECT claim_id FROM Claims
            WHERE item_id = %s AND claimant_id = %s AND claim_status = %s
        """, (item_id, user_id, 'pending'))
        existing_claim = cursor.fetchone()
        if existing_claim:
            return jsonify({"error": "You already have a pending claim for this item."}), 400

        # Insert claim record
        insert_query = """
            INSERT INTO Claims (item_id, claimant_id, verification_details, claim_status)
            VALUES (%s, %s, %s, %s)
        """
        cursor.execute(insert_query, (item_id, user_id, verification_details, 'pending'))

        # Update item status to claim_pending only if current status is not already claim_pending or resolved
        cursor.execute("SELECT status FROM Items WHERE item_id = %s", (item_id,))
        current_status = cursor.fetchone()[0]
        if current_status not in ['claim_pending', 'resolved']:
            cursor.execute("UPDATE Items SET status = %s WHERE item_id = %s", ('claim_pending', item_id))

        db.conn.commit()
        return jsonify({"message": "Claim submitted successfully."}), 201
    except mysql.connector.Error as err:
        return jsonify({"error": f"Could not submit claim. {err}"}), 500
    finally:
        cursor.close()

@item_bp.route('', methods=['GET'])
def get_all_items():
    status_filter = request.args.get('status')
    search_query = request.args.get('search', '').strip()
    include_resolved = request.args.get('include_resolved', 'false').lower() == 'true'

    cursor = db.get_cursor(dictionary=True)

    # Include resolved items if requested
    allowed_statuses = ['lost', 'found']
    if include_resolved:
        allowed_statuses.append('resolved')

    base_query = """
        SELECT i.*, u.name AS reporter_name, c.name AS category_name
        FROM Items i
        JOIN Users u ON i.reported_by = u.user_id
        JOIN Categories c ON i.category_id = c.category_id
        WHERE i.status IN ({})
    """.format(','.join(['%s'] * len(allowed_statuses)))

    params = allowed_statuses[:]
    if status_filter in allowed_statuses:
        base_query += " AND i.status = %s"
        params.append(status_filter)

    if search_query:
        base_query += " AND (i.title LIKE %s OR i.description LIKE %s)"
        like_pattern = f"%{search_query}%"
        params.extend([like_pattern, like_pattern])

    cursor.execute(base_query, tuple(params))
    items = cursor.fetchall()
    cursor.close()

    return jsonify(items), 200
