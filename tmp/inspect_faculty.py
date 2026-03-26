import sys
import os
import json

# Add project root to sys.path
sys.path.append(os.getcwd())

try:
    from database import get_db_connection
    
    def inspect_faculty():
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT name, photo FROM faculty LIMIT 5")
                    rows = cur.fetchall()
                    if not rows:
                        print("No faculty found in DB.")
                        return
                    for row in rows:
                        print(f"Name: {row['name']}, Photo: {row['photo']}")
        except Exception as e:
            print(f"DB Error: {e}")

    if __name__ == "__main__":
        inspect_faculty()
except ImportError as e:
    print(f"Import Error: {e}")
except Exception as e:
    print(f"Error: {e}")
