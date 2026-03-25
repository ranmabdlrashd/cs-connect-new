import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def get_db_connection():
    db_url = os.environ.get("NEON_DATABASE_URL") or os.environ.get("LOCAL_DATABASE_URL") or os.environ.get("DATABASE_URL")
    return psycopg2.connect(db_url) if db_url else None

def migrate():
    conn = get_db_connection()
    if not conn:
        print("No DB connection")
        return

    cur = conn.cursor()

    try:
        # Update requests table
        print("Updating requests table...")
        cur.execute("ALTER TABLE requests ADD COLUMN IF NOT EXISTS request_type TEXT DEFAULT 'reserve'")
        cur.execute("ALTER TABLE requests ADD COLUMN IF NOT EXISTS admin_feedback TEXT")
        
        # Update issues table (if needed)
        # Ensure status can handle 'pending_return' or similar if we use issues table for that
        # But we'll use requests table for all 'pending' states as requested.
        
        # Ensure library_fines table is correct
        print("Updating library_fines table...")
        cur.execute("""
        CREATE TABLE IF NOT EXISTS library_fines (
            id SERIAL PRIMARY KEY,
            student_id INTEGER,
            issue_id INTEGER,
            amount DECIMAL(10,2),
            reason TEXT,
            paid BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            paid_date TIMESTAMP,
            status TEXT,
            waived_reason TEXT,
            rate_per_day DECIMAL(10,2) DEFAULT 10.00
        )
        """)
        # If library_fines already exists, ensure issue_id column is used instead of loan_id
        cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name='library_fines' AND column_name='loan_id'")
        if cur.fetchone():
            print("Renaming loan_id to issue_id in library_fines...")
            cur.execute("ALTER TABLE library_fines RENAME COLUMN loan_id TO issue_id")

        conn.commit()
        print("Migration successful.")

    except Exception as e:
        print(f"Error during migration: {e}")
        conn.rollback()
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    migrate()
