import os
import sys

# Ensure the root directory is in sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database import get_db_connection

def add_official(name, designation, email):
    conn = get_db_connection()
    if not conn: return
    try:
        with conn.cursor() as cur:
            # Check if exists
            cur.execute("SELECT sl_no FROM faculty WHERE name = %s", (name,))
            if cur.fetchone():
                print(f"'{name}' already exists in faculty table.")
                return
            
            cur.execute(
                "INSERT INTO faculty (name, designation, email) VALUES (%s, %s, %s)",
                (name, designation, email)
            )
            conn.commit()
            print(f"Added '{name}' as '{designation}' to faculty table.")
    except Exception as e:
        print(f"Error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    officials = [
        ("Dr. Veena V.", "Principal", "principal@aisat.ac.in"),
        ("Rev. Fr. Antony Vacko Arackal", "Manager & Chairman", "manager@aisat.ac.in"),
        ("Rev. Fr. Manoj Francis Marottickal", "Assistant Manager", "asstmanager@aisat.ac.in"),
        ("Prof. Paul Ansel V.", "Vice Principal (Administration)", "admin.vp@aisat.ac.in"),
        ("Prof. Kanaka Xavier.", "Vice Principal (Academics)", "acad.vp@aisat.ac.in")
    ]
    
    for name, role, email in officials:
        add_official(name, role, email)

    print("\nOfficials added.")
