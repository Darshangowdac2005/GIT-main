import mysql.connector
import os
from dotenv import load_dotenv
from utils.security import hash_password

load_dotenv()

# Configuration from .env file
db_config = {
    'host': os.getenv('MYSQL_HOST'),
    'user': os.getenv('MYSQL_USER'),
    'password': os.getenv('MYSQL_PASSWORD'),
    'database': os.getenv('MYSQL_DB'),
    'ssl_disabled': True,
    'use_pure': True
}

# If database doesn't exist, connect without it first
try:
    db_config_temp = db_config.copy()
    del db_config_temp['database']
    temp_conn = mysql.connector.connect(**db_config_temp)
    temp_cursor = temp_conn.cursor()
    temp_cursor.execute("CREATE DATABASE IF NOT EXISTS back2u")
    temp_conn.commit()
    temp_cursor.close()
    temp_conn.close()
    print("✅ Database 'back2u' created successfully!")
except mysql.connector.Error as err:
    print(f"❌ Error creating database: {err}")
    exit(1)

class Database:
    def __init__(self):
        self.conn = None
        self.cursor = None

    def connect(self):
        try:
            self.conn = mysql.connector.connect(**db_config)
            self.cursor = self.conn.cursor(dictionary=True)
            print("✅ MySQL Database connected successfully!")
        except mysql.connector.Error as err:
            print(f"❌ Error connecting to MySQL: {err}")
            exit(1)

    def get_cursor(self, dictionary=False):
        try:
            self.conn.ping(reconnect=True)
        except mysql.connector.Error:
            print("Connection lost, reconnecting...")
            self.connect()
        return self.conn.cursor(dictionary=dictionary)

    def close(self):
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()

    def run_maintenance(self):
        """Trims tables to 3 records (except Users) and re-sequences all IDs."""
        cursor = self.get_cursor(dictionary=True)
        try:
            print("🚀 Running automated database maintenance...")
            
            # 1. Fetch all data
            cursor.execute("SELECT * FROM Users ORDER BY user_id")
            users = cursor.fetchall()
            
            cursor.execute("SELECT * FROM Categories ORDER BY category_id")
            categories = cursor.fetchall()
            
            cursor.execute("SELECT * FROM Items ORDER BY item_id")
            items = cursor.fetchall()
            
            cursor.execute("SELECT * FROM Claims ORDER BY claim_id")
            claims = cursor.fetchall()
            
            cursor.execute("SELECT * FROM Notifications ORDER BY notification_id")
            notifications = cursor.fetchall()
            
            # 2. Truncate tables (disable FK checks first)
            cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
            cursor.execute("TRUNCATE TABLE Notifications")
            cursor.execute("TRUNCATE TABLE Claims")
            cursor.execute("TRUNCATE TABLE Items")
            cursor.execute("TRUNCATE TABLE Categories")
            cursor.execute("TRUNCATE TABLE Users")
            
            # 3. Re-insert with new IDs and build maps
            user_id_map = {}
            for u in users:
                old_id = u['user_id']
                cursor.execute(
                    "INSERT INTO Users (user_id, name, email, role, password_hash) VALUES (%s, %s, %s, %s, %s)",
                    (None, u['name'], u['email'], u['role'], u['password_hash'])
                )
                user_id_map[old_id] = cursor.lastrowid
                
            category_id_map = {}
            for c in categories:
                old_id = c['category_id']
                cursor.execute("INSERT INTO Categories (category_id, name) VALUES (%s, %s)", (None, c['name']))
                category_id_map[old_id] = cursor.lastrowid
                
            item_id_map = {}
            for it in items:
                old_id = it['item_id']
                new_reported_by = user_id_map.get(it['reported_by'])
                new_category_id = category_id_map.get(it['category_id'])
                if new_reported_by and new_category_id:
                    cursor.execute(
                        "INSERT INTO Items (item_id, reported_by, category_id, title, description, status, date_reported) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                        (None, new_reported_by, new_category_id, it['title'], it['description'], it['status'], it['date_reported'])
                    )
                    item_id_map[old_id] = cursor.lastrowid
                
            for cl in claims:
                new_item_id = item_id_map.get(cl['item_id'])
                new_claimant_id = user_id_map.get(cl['claimant_id'])
                if new_item_id and new_claimant_id:
                    cursor.execute(
                        "INSERT INTO Claims (claim_id, item_id, claimant_id, claim_status, verification_details, claimed_at) VALUES (%s, %s, %s, %s, %s, %s)",
                        (None, new_item_id, new_claimant_id, cl['claim_status'], cl['verification_details'], cl['claimed_at'])
                    )
                    
            for n in notifications:
                new_user_id = user_id_map.get(n['user_id'])
                if new_user_id:
                    cursor.execute(
                        "INSERT INTO Notifications (notification_id, user_id, message, type, status, created_at) VALUES (%s, %s, %s, %s, %s, %s)",
                        (None, new_user_id, n['message'], n['type'], n['status'], n['created_at'])
                    )

            cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
            self.conn.commit()
            print("✅ Maintenance completed: Sequential IDs & Trimmed data.")
            
        except Exception as e:
            print(f"❌ Maintenance failed: {e}")
            self.conn.rollback()
        finally:
            cursor.close()

db = Database()
db.connect()

def create_tables_and_seed():
    cursor = db.get_cursor()
    item_ids = []
    
    # --- 1. Users Table ---
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Users (
            user_id INT PRIMARY KEY AUTO_INCREMENT,
            name VARCHAR(100) NOT NULL,
            email VARCHAR(100) UNIQUE NOT NULL,
            role ENUM('student', 'faculty', 'admin') NOT NULL DEFAULT 'student',
            password_hash VARCHAR(255) NOT NULL
        )
    """)
    
    # --- 2. Categories Table ---
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Categories (
            category_id INT PRIMARY KEY AUTO_INCREMENT,
            name VARCHAR(50) UNIQUE NOT NULL
        )
    """)
    
    # --- 3. Items Table ---
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Items (
            item_id INT PRIMARY KEY AUTO_INCREMENT,
            reported_by INT NOT NULL,
            category_id INT NOT NULL,
            title VARCHAR(100) NOT NULL,
            description TEXT,
            status ENUM('lost', 'found', 'claim_pending', 'resolved') NOT NULL,
            date_reported DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (reported_by) REFERENCES Users(user_id) ON UPDATE CASCADE,
            FOREIGN KEY (category_id) REFERENCES Categories(category_id) ON UPDATE CASCADE
        )
    """)
    
    # --- 4. Claims Table ---
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Claims (
            claim_id INT PRIMARY KEY AUTO_INCREMENT,
            item_id INT NOT NULL,
            claimant_id INT NOT NULL,
            claim_status ENUM('pending', 'approved', 'rejected') NOT NULL DEFAULT 'pending',
            verification_details TEXT,
            claimed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (item_id) REFERENCES Items(item_id) ON UPDATE CASCADE,
            FOREIGN KEY (claimant_id) REFERENCES Users(user_id) ON UPDATE CASCADE
        )
    """)
    
    # --- 5. Notifications Table ---
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Notifications (
            notification_id INT PRIMARY KEY AUTO_INCREMENT,
            user_id INT NOT NULL, 
            message TEXT NOT NULL,
            type ENUM('email', 'system') NOT NULL,
            status ENUM('sent', 'pending', 'read') NOT NULL DEFAULT 'pending',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES Users(user_id) ON UPDATE CASCADE
        )
    """)
    
    # --- Add the MySQL trigger to update Items.status when a claim is approved ---
    try:
        cursor.execute("DROP TRIGGER IF EXISTS update_item_status_on_claim_approval")
        cursor.execute("""
            CREATE TRIGGER update_item_status_on_claim_approval
            AFTER UPDATE ON Claims
            FOR EACH ROW
            BEGIN
                IF NEW.claim_status = 'approved' THEN
                    UPDATE Items SET status = 'resolved' WHERE item_id = NEW.item_id;
                END IF;
            END;
        """)
        print("✅ Trigger 'update_item_status_on_claim_approval' created successfully.")
    except mysql.connector.Error as err:
        print(f"❌ Failed to create trigger: {err}")
    
    # Seed categories if empty
    cursor.execute("SELECT COUNT(*) FROM Categories")
    count = cursor.fetchone()[0]
    print(f"Categories table has {count} entries.")
    if count == 0:
        categories = ['Electronics', 'Clothing', 'Books', 'Accessories', 'Other']
        print(f"🌱 Seeding {len(categories)} default categories...")
        for cat in categories:
            try:
                cursor.execute("INSERT INTO Categories (name) VALUES (%s)", (cat,))
                print(f"✅ Inserted category: {cat}")
            except mysql.connector.Error as err:
                print(f"❌ Failed to insert category '{cat}': {err}")
                # Continue with other categories even if one fails
        print("Category seeding completed.")
    else:
        print("✅ Categories already seeded.")

    # Only ensure tables exist; do not insert any sample data
    db.conn.commit()
    cursor.close()
    print("✅ Database tables checked/created successfully.")
