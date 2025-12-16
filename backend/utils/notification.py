# backend/utils/notification.py

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from dotenv import load_dotenv

from config.db_connector import db
from models.notification_model import Notification

load_dotenv()

def get_user_email(user_id):
    """Fetches user email and name from the database."""
    try:
        cursor = db.get_cursor(dictionary=True)
        cursor.execute("SELECT email, name FROM Users WHERE user_id = %s", (user_id,))
        user = cursor.fetchone()
        cursor.close()
        if not user:
            print(f"Warning: User with ID {user_id} not found.")
            return None
        return user
    except Exception as e:
        print(f"Error fetching user {user_id}: {e}")
        return None

def send_email(recipient_email, subject, body):
    """Handles SMTP connection and sends the email."""
    # Skip email sending if credentials not configured
    sender_email = os.getenv('EMAIL_SENDER')
    email_host = os.getenv('EMAIL_HOST')
    email_user = os.getenv('EMAIL_USER')
    email_pass = os.getenv('EMAIL_PASS')

    if not all([sender_email, email_host, email_user, email_pass]):
        missing = []
        if not sender_email: missing.append('EMAIL_SENDER')
        if not email_host: missing.append('EMAIL_HOST')
        if not email_user: missing.append('EMAIL_USER')
        if not email_pass: missing.append('EMAIL_PASS')
        print(f"Email credentials not configured. Missing: {', '.join(missing)}")
        print(f"Would have sent to {recipient_email}: {subject}")
        return True  # Return True to continue flow
    
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = recipient_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    try:
        server = smtplib.SMTP(os.getenv('EMAIL_HOST'), int(os.getenv('EMAIL_PORT', 587)))
        server.starttls()  
        server.login(os.getenv('EMAIL_USER'), os.getenv('EMAIL_PASS'))
        server.sendmail(sender_email, recipient_email, msg.as_string())
        server.quit()
        with open("email_debug.log", "a") as f:
            f.write(f"SUCCESS: Sent to {recipient_email}\n")
        return True
    except Exception as e:
        error_msg = f"ERROR sending email to {recipient_email}: {e}"
        print(error_msg)
        with open("email_debug.log", "a") as f:
            f.write(f"{error_msg}\n")
        return False

def insert_notification(user_id, message, notification_type):
    """Logs the notification in the database."""
    cursor = db.get_cursor()
    query = "INSERT INTO Notifications (user_id, message, type, status) VALUES (%s, %s, %s, %s)"
    cursor.execute(query, (user_id, message, notification_type, Notification.STATUSES['SENT']))
    db.conn.commit()
    cursor.close()

def send_claim_resolved_emails(item_id, claimant_id, admin_id):
    """Sends resolution emails to both the reporter and the claimant."""
    try:
        cursor = db.get_cursor(dictionary=True)

        # 1. Get Item Reporter (Original Lost/Found User)
        cursor.execute("SELECT reported_by, title FROM Items WHERE item_id = %s", (item_id,))
        item_info = cursor.fetchone()
        if not item_info:
            print(f"Warning: Item with ID {item_id} not found.")
            cursor.close()
            return
        reporter_id = item_info['reported_by']
        item_title = item_info['title']

        reporter = get_user_email(reporter_id)
        claimant = get_user_email(claimant_id)

        cursor.close()

        if not reporter or not claimant:
            print("Warning: Missing user data for reporter or claimant. Skipping email notifications.")
            return

        # Email to Original Reporter (Item Found/Returned)
        reporter_subject = f"SUCCESS: Your Item '{item_title}' Has Been RESOLVED!"
        reporter_body = f"Hello {reporter['name']},\n\nGood news! Your item, '{item_title}', has been verified by the Admin (ID: {admin_id}) and matched with the person who found it. Please contact the claimant, {claimant['name']}, to arrange collection. Your contact details have been shared with them."

        if send_email(reporter['email'], reporter_subject, reporter_body):
            insert_notification(reporter_id, "Item successfully matched and resolved. Check your email for details!", Notification.TYPES['EMAIL'])

        # Email to Claimant (Verification Approved)
        claimant_subject = f"SUCCESS: Your Claim on '{item_title}' Has Been APPROVED!"
        claimant_body = f"Hello {claimant['name']},\n\nYour claim on '{item_title}' has been successfully approved! Please contact the original reporter, {reporter['name']}, to arrange the return of the item. Their email is {reporter['email']}."

        if send_email(claimant['email'], claimant_subject, claimant_body):
            insert_notification(claimant_id, "Claim approved. Check your email for reporter's contact info.", Notification.TYPES['EMAIL'])
    except Exception as e:
        print(f"Error in send_claim_resolved_emails: {e}")
