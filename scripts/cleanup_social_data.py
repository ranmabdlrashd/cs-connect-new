import json
import os
import sys

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database import get_db_connection

EXCLUDE_TERMS = [
    "facebook",
    "instagram",
    "youtube",
    "linkedin",
    "telegram",
    "ktunotes",
    "upload notes",
    "micro"
]

def clean_subjects_list(subjects):
    cleaned = []
    for subj in subjects:
        name_lower = subj.get("name", "").lower()
        if not any(term in name_lower for term in EXCLUDE_TERMS):
            cleaned.append(subj)
    return cleaned

def clean_database():
    print("Cleaning 'semesters' table in the database...")
    conn = get_db_connection()
    if conn is None:
        print("Could not connect to database.")
        return
        
    try:
        cur = conn.cursor()
        from psycopg2.extras import DictCursor
        cur = conn.cursor(cursor_factory=DictCursor)
        cur.execute("SELECT sl_no, subjects FROM semesters")
        rows = cur.fetchall()
        for row in rows:
            sl_no = row['sl_no']
            if row['subjects']:
                subjects = json.loads(row['subjects'])
                cleaned_subjects = clean_subjects_list(subjects)
                cur.execute(
                    "UPDATE semesters SET subjects = %s WHERE sl_no = %s",
                    (json.dumps(cleaned_subjects), sl_no)
                )
        conn.commit()
        print("Database 'semesters' table cleaned successfully.")
    except Exception as e:
        print(f"Error cleaning database: {e}")
    finally:
        conn.close()

def clean_json_file():
    filepath = 'tmp/all_notes.json'
    print(f"Cleaning JSON file: {filepath}")
    if not os.path.exists(filepath):
        print(f"File not found: {filepath}")
        return
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        cleaned_data = {}
        for sem, subjects in data.items():
            cleaned_data[sem] = clean_subjects_list(subjects)
            
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(cleaned_data, f, indent=4)
        print("JSON file cleaned successfully.")
    except Exception as e:
        print(f"Error cleaning JSON file: {e}")

if __name__ == "__main__":
    clean_database()
    clean_json_file()
