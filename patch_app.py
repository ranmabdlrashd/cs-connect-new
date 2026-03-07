import re

with open("app.py", "r", encoding="utf-8") as f:
    content = f.read()

# 1. Imports
content = re.sub(
    r"^import sqlite3\n",
    "import psycopg2\nimport psycopg2.extras\n",
    content,
    flags=re.MULTILINE
)

# 2. Database variable -> Connection class
db_class = """
# PostgreSQL Connection details
DB_HOST = "localhost"
DB_NAME = "login"
DB_USER = "postgres"
DB_PASS = "1234"

class DBConnection:
    def __init__(self):
        self.conn = psycopg2.connect(
            host=DB_HOST, dbname=DB_NAME, user=DB_USER, password=DB_PASS
        )
    
    def cursor(self):
        return self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
    def execute(self, query, params=None):
        cur = self.cursor()
        if params:
            cur.execute(query, params)
        else:
            cur.execute(query)
        return cur
        
    def commit(self):
        self.conn.commit()
        
    def close(self):
        self.conn.close()

def get_db_connection():
    return DBConnection()
"""

# Replace DATABASE global with the connection proxy
content = re.sub(r'DATABASE\s*=\s*"csconnect\.db"', db_class, content)

# 3. get_db_connection removal
old_get_conn = """def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn"""
content = content.replace(old_get_conn, "")

# 4. sqlite3.connect -> get_db_connection()
content = content.replace("sqlite3.connect(DATABASE)", "get_db_connection()")

# 5. sqlite3.IntegrityError -> psycopg2.IntegrityError
content = content.replace("sqlite3.IntegrityError", "psycopg2.IntegrityError")

# 6. AUTOINCREMENT -> SERIAL
content = content.replace("AUTOINCREMENT", "SERIAL")

# 7. Replace '?' with '%s' in SQL queries
# Using regex to target '?' used for SQL bindings
content = re.sub(r'(\s|\(|,)\?(\s|\)|,)', r'\1%s\2', content)

with open("app.py", "w", encoding="utf-8") as f:
    f.write(content)

print("app.py patched successfully")
