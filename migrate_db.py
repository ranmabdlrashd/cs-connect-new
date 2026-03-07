import sqlite3
import psycopg2
import sys

# PostgreSQL configuration
PG_HOST = "localhost"
PG_DBNAME = "login"
PG_USER = "postgres"
PG_PASSWORD = "1234"

SQLITE_DB = "csconnect.db"

# Schema mapping from SQLite to PostgreSQL
TABLE_SCHEMAS = {
    "users": """
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            user_id TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            role TEXT DEFAULT 'student'
        )
    """,
    "faculty": """
        CREATE TABLE IF NOT EXISTS faculty (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            designation TEXT,
            designation_key TEXT,
            qualification TEXT,
            joined TEXT,
            research TEXT,
            email TEXT,
            photo TEXT
        )
    """,
    "books": """
        CREATE TABLE IF NOT EXISTS books (
            id SERIAL PRIMARY KEY,
            title TEXT NOT NULL,
            author TEXT,
            category TEXT,
            status TEXT,
            shelf TEXT,
            cover_gradient TEXT,
            cover_icon TEXT
        )
    """,
    "placement_summary": """
        CREATE TABLE IF NOT EXISTS placement_summary (
            id SERIAL PRIMARY KEY,
            icon TEXT,
            value TEXT,
            label TEXT,
            decimal_bool INTEGER,
            company TEXT
        )
    """,
    "placement_companies": """
        CREATE TABLE IF NOT EXISTS placement_companies (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            url TEXT,
            sector TEXT
        )
    """,
    "alumni": """
        CREATE TABLE IF NOT EXISTS alumni (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            batch TEXT,
            company TEXT,
            package TEXT,
            photo TEXT,
            testimonial TEXT
        )
    """,
    "internships": """
        CREATE TABLE IF NOT EXISTS internships (
            id SERIAL PRIMARY KEY,
            title TEXT NOT NULL,
            company TEXT,
            domain TEXT,
            location TEXT,
            description TEXT,
            link TEXT
        )
    """,
    "programs": """
        CREATE TABLE IF NOT EXISTS programs (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            duration TEXT,
            intake TEXT,
            eligibility TEXT,
            extra_icon TEXT,
            extra_label TEXT,
            extra_value TEXT,
            highlights TEXT
        )
    """,
    "semesters": """
        CREATE TABLE IF NOT EXISTS semesters (
            id SERIAL PRIMARY KEY,
            title TEXT NOT NULL,
            subjects TEXT
        )
    """
}

def migrate():
    print("Connecting to SQLite...")
    sqlite_conn = sqlite3.connect(SQLITE_DB)
    sqlite_cursor = sqlite_conn.cursor()

    print(f"Connecting to PostgreSQL (Host: {PG_HOST}, DB: {PG_DBNAME}, User: {PG_USER})...")
    try:
        pg_conn = psycopg2.connect(
            host=PG_HOST,
            dbname=PG_DBNAME,
            user=PG_USER,
            password=PG_PASSWORD
        )
        pg_cursor = pg_conn.cursor()
    except Exception as e:
        print(f"Failed to connect to PostgreSQL: {e}")
        print("Please check your PostgreSQL credentials and make sure the database exists.")
        sys.exit(1)

    for table, schema in TABLE_SCHEMAS.items():
        print(f"Migrating table: {table} ...")
        
        # Create table in PostgreSQL
        pg_cursor.execute(schema)
        
        # Fetch data from SQLite
        sqlite_cursor.execute(f"SELECT * FROM {table}")
        rows = sqlite_cursor.fetchall()
        
        if not rows:
            print(f"  - No data found in SQLite table '{table}', skipping insert.")
            continue
        
        # SQLite's id is included, we can insert it directly to keep associations (though not strictly necessary here as no foreign keys are used)
        # Getting column names to formulate the INSERT query
        sqlite_cursor.execute(f"PRAGMA table_info({table})")
        columns = [info[1] for info in sqlite_cursor.fetchall()]
        col_names = ", ".join(columns)
        placeholders = ", ".join(["%s"] * len(columns))
        
        insert_query = f"INSERT INTO {table} ({col_names}) VALUES ({placeholders})"
        
        # Truncate existing data in pg table before insert to avoid primary key conflicts 
        # (if running script multiple times)
        pg_cursor.execute(f"TRUNCATE TABLE {table} RESTART IDENTITY CASCADE;")
        
        print(f"  - Inserts {len(rows)} records into PostgreSQL '{table}'...")
        try:
            pg_cursor.executemany(insert_query, rows)
        except Exception as e:
            print(f"  - Error inserting into {table}: {e}")
            pg_conn.rollback()
            continue

    # Commit changes to PostgreSQL
    pg_conn.commit()
    print("\nMigration completed successfully!")
    
    sqlite_conn.close()
    pg_conn.close()

if __name__ == "__main__":
    migrate()
