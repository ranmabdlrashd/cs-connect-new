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

def audit_admin_routes():
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Audit events table - change id to sl_no if it exists as id
    cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'events' AND column_name = 'id'")
    if cur.fetchone():
        print("Migrating 'events' table: id -> sl_no")
        cur.execute("ALTER TABLE events RENAME COLUMN id TO sl_no")
        conn.commit()

    # Check for other tables and migrate if necessary
    tables_to_check = ['notices', 'placement_drives', 'placement_applications', 'lab_bookings', 'labs', 'timetable_slots', 'fee_records', 'mark_submissions', 'subjects']
    for table in tables_to_check:
        cur.execute("SELECT table_name FROM information_schema.tables WHERE table_name = %s", (table,))
        if cur.fetchone():
            cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name = %s AND column_name = 'id'", (table,))
            if cur.fetchone():
                print(f"Migrating '{table}' table: id -> sl_no")
                cur.execute(f"ALTER TABLE {table} RENAME COLUMN id TO sl_no")
                conn.commit()
        else:
            print(f"Table '{table}' does not exist - skipping migration check.")

    conn.close()

if __name__ == "__main__":
    audit_admin_routes()
