import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

db_url = os.environ.get("NEON_DATABASE_URL") or os.environ.get("LOCAL_DATABASE_URL") or os.environ.get("DATABASE_URL")

if db_url:
    conn = psycopg2.connect(db_url)
else:
    DB_HOST = os.environ.get("DB_HOST", "localhost")
    DB_NAME = os.environ.get("DB_NAME", "csconnect")
    DB_USER = os.environ.get("DB_USER", "postgres")
    DB_PASS = os.environ.get("DB_PASS", "1234")
    conn = psycopg2.connect(host=DB_HOST, dbname=DB_NAME, user=DB_USER, password=DB_PASS)

cursor = conn.cursor()
print("Applying database fixes for requests table...")
cursor.execute("ALTER TABLE requests ADD COLUMN IF NOT EXISTS request_type TEXT DEFAULT 'reserve'")
cursor.execute("ALTER TABLE requests ADD COLUMN IF NOT EXISTS admin_feedback TEXT")
conn.commit()
conn.close()
print("Fixed successfully!")
