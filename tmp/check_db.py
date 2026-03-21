import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def get_db_connection():
    db_url = os.environ.get("NEON_DATABASE_URL") or os.environ.get("LOCAL_DATABASE_URL") or os.environ.get("DATABASE_URL")
    return psycopg2.connect(db_url) if db_url else None

conn = get_db_connection()
if not conn:
    print("No DB connection")
    exit(1)

cur = conn.cursor()

# Get all tables
cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public'")
tables = [row[0] for row in cur.fetchall()]
print("Tables:", tables)

# For each table, get columns
for t in ["books", "library_loans", "library_fines", "book_reservations", "notices"]:
    if t in tables:
        print(f"\n--- {t} ---")
        cur.execute(f"SELECT column_name, data_type FROM information_schema.columns WHERE table_name='{t}'")
        for col in cur.fetchall():
            print(col[0], col[1])
    else:
        print(f"\nTable {t} DOES NOT EXIST.")

conn.close()
