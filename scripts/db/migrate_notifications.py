import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

import sys
# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from database import db_connection

def migrate():
    try:
        with db_connection() as conn:
            cur = conn.cursor()
        
        # Check if table exists
        cur.execute("SELECT to_regclass('public.notifications')")
        exists = cur.fetchone()[0]
        
        if exists:
            # 1. Add title and category columns
            cur.execute("ALTER TABLE notifications ADD COLUMN IF NOT EXISTS title TEXT DEFAULT 'Notice';")
            cur.execute("ALTER TABLE notifications ADD COLUMN IF NOT EXISTS category TEXT DEFAULT 'Academic';")
            
            # 2. Rename columns using a safer approach: check if they exist before renaming
            cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name='notifications'")
            columns = [col[0] for col in cur.fetchall()]
            
            if 'message' in columns and 'body' not in columns:
                cur.execute("ALTER TABLE notifications RENAME COLUMN message TO body;")
            
            if 'read_status' in columns and 'is_read' not in columns:
                cur.execute("ALTER TABLE notifications RENAME COLUMN read_status TO is_read;")
            
            conn.commit()
            print("Successfully migrated notifications table.")
        else:
            print("Table notifications does not exist yet. It will be created on app startup.")
    except Exception as e:
        print(f"Error during migration: {e}")

if __name__ == '__main__':
    migrate()
