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

def check_missing_tables():
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Tables referenced in admin_routes.py
    tables = [
        'users', 'mark_submissions', 'subjects', 'results', 'settings', 'notices', 'events', 
        'placement_drives', 'placement_applications', 'placement_stats', 'labs', 'lab_bookings', 
        'timetable_status', 'timetable_slots', 'fee_records', 'portal_sessions', 'issues'
    ]
    
    print("Checking for tables in all schemas:")
    for table in tables:
        cur.execute("SELECT table_schema FROM information_schema.tables WHERE table_name = %s", (table,))
        schemas = [row[0] for row in cur.fetchall()]
        if schemas:
            print(f"  [FOUND] {table} in schemas: {', '.join(schemas)}")
        else:
            print(f"  [MISSING] {table} NOT FOUND")
            
    conn.close()

if __name__ == "__main__":
    check_missing_tables()
