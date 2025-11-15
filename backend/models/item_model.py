# backend/models/item_model.py

class Item:
    TABLE_NAME = "Items"
    
    # Item statuses defined in the ENUM
    STATUSES = {
        'LOST': 'lost',
        'FOUND': 'found',
        'CLAIM_PENDING': 'claim_pending',
        'RESOLVED': 'resolved',
    }