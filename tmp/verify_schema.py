import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def get_db_connection():
    urls = [
        os.environ.get("NEON_DATABASE_URL"),
        os.environ.get("LOCAL_DATABASE_URL"),
        os.environ.get("DATABASE_URL")
    ]
    for url in urls:
        if url:
            try:
                return psycopg2.connect(url)
            except:
                continue
    return None

conn = get_db_connection()
if not conn:
    print("No DB connection")
    exit(1)

cur = conn.cursor()
table = "library_fines"
print(f"--- Columns in {table} ---")
cur.execute(f"SELECT column_name, data_type FROM information_schema.columns WHERE table_name='{table}'")
for col in cur.fetchall():
    print(col[0], col[1])

conn.close()
