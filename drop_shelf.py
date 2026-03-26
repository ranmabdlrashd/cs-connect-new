import psycopg2
from dotenv import load_dotenv
import os

load_dotenv()

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_NAME = os.getenv("DB_NAME", "csconnect")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASS = os.getenv("DB_PASS", "postgres")

def drop_shelf():
    conn = psycopg2.connect(host=DB_HOST, dbname=DB_NAME, user=DB_USER, password=DB_PASS)
    cursor = conn.cursor()
    try:
        cursor.execute("ALTER TABLE books DROP COLUMN IF EXISTS shelf")
        cursor.execute("ALTER TABLE books DROP COLUMN IF EXISTS shelf_location")
        conn.commit()
        print("Shelf columns dropped successfully.")
    except Exception as e:
        print(f"Error: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    drop_shelf()
