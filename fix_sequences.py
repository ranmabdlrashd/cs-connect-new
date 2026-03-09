import psycopg2
from dotenv import load_dotenv
import os

load_dotenv()

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_NAME = os.getenv("DB_NAME", "csconnect")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASS = os.getenv("DB_PASS", "postgres")

def fix_sequences():
    conn = psycopg2.connect(host=DB_HOST, dbname=DB_NAME, user=DB_USER, password=DB_PASS)
    cursor = conn.cursor()
    
    tables = [
        "users", "faculty", "books", "programs", "semesters", "news_ticker", 
        "alumni", "internships", "placement_companies", "placement_summary",
        "issues", "requests", "notifications"
    ]
    
    try:
        for table in tables:
            # Check if table exists
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' AND table_name = %s
                );
            """, (table,))
            exists = cursor.fetchone()[0]
            
            if exists:
                cursor.execute(f"SELECT setval(pg_get_serial_sequence('{table}', 'id'), coalesce(max(id), 1), max(id) IS NOT null) FROM {table};")
                print(f"Fixed sequence for table: {table}")
                
        conn.commit()
        print("All sequences fixed successfully.")
    except Exception as e:
        print(f"Error: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    fix_sequences()
