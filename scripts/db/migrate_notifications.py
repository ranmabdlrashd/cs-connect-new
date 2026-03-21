import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

def get_db_connection():
    db_url = os.environ.get("NEON_DATABASE_URL") or os.environ.get("LOCAL_DATABASE_URL") or os.environ.get("DATABASE_URL")
    if db_url:
        return psycopg2.connect(db_url)
    else:
        DB_HOST = os.environ.get("DB_HOST", "localhost")
        DB_NAME = os.environ.get("DB_NAME", "csconnect")
        DB_USER = os.environ.get("DB_USER", "postgres")
        DB_PASS = os.environ.get("DB_PASS", "1234")
        return psycopg2.connect(
            host=DB_HOST, dbname=DB_NAME, user=DB_USER, password=DB_PASS
        )

def migrate():
    try:
        conn = get_db_connection()
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
            
        conn.close()
    except Exception as e:
        print(f"Error during migration: {e}")

if __name__ == '__main__':
    migrate()
