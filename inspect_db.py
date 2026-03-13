import os
import psycopg2
import sys
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

# Force UTF-8 encoding for Windows console
if sys.platform == "win32":
    import codecs
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())

load_dotenv()

def inspect_site_data():
    db_url = os.environ.get("NEON_DATABASE_URL")
    if not db_url:
        print("NEON_DATABASE_URL not found in .env")
        return

    try:
        conn = psycopg2.connect(db_url)
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT key, data FROM site_data;")
            rows = cur.fetchall()
            
            if not rows:
                print("The site_data table is empty.")
            else:
                print(f"Found {len(rows)} records in site_data:\n")
                for row in rows:
                    key = row['key']
                    data_str = str(row['data'])
                    preview = data_str[:200] + "..." if len(data_str) > 200 else data_str
                    print(f"Key: {key}")
                    print(f"Data Preview: {preview}\n")
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    inspect_site_data()

if __name__ == "__main__":
    inspect_site_data()
