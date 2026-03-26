import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def get_db_connection():
    db_url = os.environ.get("NEON_DATABASE_URL") or os.environ.get("LOCAL_DATABASE_URL") or os.environ.get("DATABASE_URL")
    if db_url:
        return psycopg2.connect(db_url)
    return psycopg2.connect(
        host=os.environ.get("DB_HOST", "localhost"),
        dbname=os.environ.get("DB_NAME", "csconnect"),
        user=os.environ.get("DB_USER", "postgres"),
        password=os.environ.get("DB_PASS", "1234")
    )

def check_tables():
    conn = get_db_connection()
    cur = conn.cursor()
    
    tables = [
        'users', 'faculty', 'books', 'issues', 'requests', 'notices', 'events', 
        'placement_drives', 'subjects', 'labs', 'lab_bookings', 'timetable_slots', 'fee_records'
    ]
    for table in tables:
        print(f"\nChecking table: {table}")
        query = f"SELECT column_name FROM information_schema.columns WHERE table_name = '{table}' AND table_schema = 'public'"
        cur.execute(query)
        columns = [row[0] for row in cur.fetchall()]
        print(f"  Columns: {', '.join(columns)}")
        if 'sl_no' in columns:
            print("  [OK] has sl_no")
        elif 'id' in columns:
            print("  [LEGACY] has id")
        else:
            print("  [MISSING] No sl_no or id found")
    
    conn.close()

if __name__ == "__main__":
    check_tables()
