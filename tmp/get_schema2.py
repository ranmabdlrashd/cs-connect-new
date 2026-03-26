import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app import get_db_connection

def main():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_name='download_logs'")
        print("Download Logs:", cur.fetchall())
    except Exception as e:
        print("Error:", e)

if __name__ == '__main__':
    main()
