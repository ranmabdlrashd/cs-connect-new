"""Rename lab timetable batch names in all three tables."""
import os, psycopg2
from dotenv import load_dotenv
load_dotenv()

db_url = (os.environ.get("NEON_DATABASE_URL")
          or os.environ.get("LOCAL_DATABASE_URL")
          or os.environ.get("DATABASE_URL"))
conn = psycopg2.connect(db_url)
cur = conn.cursor()

RENAMES = [
    ("Lab A402 (S2,S8,S4)", "Network Programming Lab"),
    ("Lab A402 (S2)",        "Database Lab"),
    ("Lab A401 (S4,S2,S8)", "Programming Lab"),
    ("Lab DB (S2,S4,S6)",   "Computer Systems Lab"),
]

for old, new in RENAMES:
    cur.execute("UPDATE timetable_meta     SET batch=%s WHERE batch=%s", (new, old))
    cur.execute("UPDATE timetable_subjects SET batch=%s WHERE batch=%s", (new, old))
    cur.execute("UPDATE timetable          SET batch=%s WHERE batch=%s", (new, old))
    print(f"  ✅ '{old}' → '{new}'")

conn.commit()
cur.close()
conn.close()
print("Done!")
