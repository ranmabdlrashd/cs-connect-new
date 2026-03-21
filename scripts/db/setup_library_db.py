import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def get_db_connection():
    db_url = os.environ.get("NEON_DATABASE_URL") or os.environ.get("LOCAL_DATABASE_URL") or os.environ.get("DATABASE_URL")
    return psycopg2.connect(db_url) if db_url else None

def setup_library_tables():
    conn = get_db_connection()
    if not conn:
        print("No DB connection")
        return

    cur = conn.cursor()

    try:
        # Alter library_loans to add issued_date and returned_date if not present
        cur.execute("ALTER TABLE library_loans ADD COLUMN IF NOT EXISTS issued_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
        cur.execute("ALTER TABLE library_loans ADD COLUMN IF NOT EXISTS returned_date TIMESTAMP")

        # Create library_fines table
        cur.execute("""
        CREATE TABLE IF NOT EXISTS library_fines (
            id SERIAL PRIMARY KEY,
            student_id INTEGER,
            loan_id INTEGER,
            amount DECIMAL(10,2),
            reason TEXT,
            paid BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        # Create book_reservations table
        cur.execute("""
        CREATE TABLE IF NOT EXISTS book_reservations (
            id SERIAL PRIMARY KEY,
            student_id INTEGER,
            book_id INTEGER,
            status TEXT DEFAULT 'waiting',
            queue_position INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        # Create notices table
        cur.execute("""
        CREATE TABLE IF NOT EXISTS notices (
            id SERIAL PRIMARY KEY,
            title TEXT,
            category TEXT,
            content TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        conn.commit()
        print("Successfully updated database schema for library.")

    except Exception as e:
        print(f"Error: {e}")
        conn.rollback()
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    setup_library_tables()
