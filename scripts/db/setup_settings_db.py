import database
import psycopg2

def setup_settings_fields():
    print("Setting up new user profile and notification preference fields...")
    conn = database.get_db_connection()
    if not conn:
        print("Failed to connect to database.")
        return

    cursor = conn.cursor()
    
    commands = [
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS phone TEXT",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS attendance_alerts BOOLEAN DEFAULT TRUE",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS assignment_alerts BOOLEAN DEFAULT TRUE",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS library_alerts BOOLEAN DEFAULT TRUE",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS placement_alerts BOOLEAN DEFAULT TRUE",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS department_notices BOOLEAN DEFAULT FALSE",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS exam_alerts BOOLEAN DEFAULT TRUE"
    ]
    
    try:
        for cmd in commands:
            cursor.execute(cmd)
            print(f"Executed: {cmd}")
        
        conn.commit()
        print("Successfully added settings columns to users table.")
    except Exception as e:
        print(f"Error executing migration: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    setup_settings_fields()
