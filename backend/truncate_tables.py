from config.db_connector import db

def truncate_tables():
    cursor = db.get_cursor()
    # Order matters due to foreign key constraints: truncate child tables first
    tables = ['Claims', 'Notifications', 'Items', 'Categories', 'Users']
    for table in tables:
        try:
            cursor.execute(f"DELETE FROM {table}")
            print(f"✅ Deleted data from table: {table}")
        except Exception as e:
            print(f"❌ Error deleting from {table}: {e}")
    db.conn.commit()
    cursor.close()
    print("✅ All table data deleted successfully.")

if __name__ == "__main__":
    truncate_tables()
