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
    
    tables = ['users', 'faculty', 'books', 'issues', 'requests']
    for table in tables:
        print(f"\nChecking table: {table}")
        query = f"SELECT column_name, data_type FROM information_schema.columns WHERE table_name = '{table}' AND table_schema = 'public'"
        cur.execute(query)
        columns = cur.fetchall()
        for col in columns:
            print(f"  - {col[0]} ({col[1]})")
    
    conn.close()

if __name__ == "__main__":
    check_tables()
