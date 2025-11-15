# backend/models/claim_model.py

class Claim:
    TABLE_NAME = "Claims"
    
    # Claim statuses defined in the ENUM
    STATUSES = {
        'PENDING': 'pending',
        'APPROVED': 'approved',
        'REJECTED': 'rejected',
    }