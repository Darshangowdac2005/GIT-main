# backend/models/notification_model.py

class Notification:
    TABLE_NAME = "Notifications"
    
    # Notification types and statuses
    TYPES = {
        'EMAIL': 'email',
        'SYSTEM': 'system',
    }
    
    STATUSES = {
        'SENT': 'sent',
        'PENDING': 'pending',
        'READ': 'read',
    }