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

def list_tables():
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
    tables = [row[0] for row in cur.fetchall()]
    print(f"Tables in public schema: {', '.join(tables)}")
    
    conn.close()

if __name__ == "__main__":
    list_tables()
