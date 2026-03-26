import sys
import os

# Add the project root to sys.path so we can import app
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import get_db_connection

def main():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_name='resources'")
        print("Resources:", cur.fetchall())
        
        cur.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_name='resource_downloads'")
        print("Resource Downloads:", cur.fetchall())
        
    except Exception as e:
        print("Error:", e)

if __name__ == '__main__':
    main()
