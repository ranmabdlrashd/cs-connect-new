import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database import get_db_connection

def check():
    conn = get_db_connection()
    cur = conn.cursor()
    for table in ['internal_marks', 'student_performance', 'student_semester_gpas']:
        cur.execute(f"SELECT column_name, data_type FROM information_schema.columns WHERE table_name = '{table}'")
        print(f"{table}:", cur.fetchall())
    conn.close()

if __name__ == "__main__":
    check()
