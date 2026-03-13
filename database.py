import os
from typing import Dict, List
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def get_db_connection():
    """
    Establish and return a connection to the PostgreSQL database.
    Favors NEON_DATABASE_URL, then LOCAL_DATABASE_URL, then DATABASE_URL.
    """
    db_url = os.environ.get("NEON_DATABASE_URL") or os.environ.get("LOCAL_DATABASE_URL") or os.environ.get("DATABASE_URL")
    
    try:
        if db_url:
            conn = psycopg2.connect(db_url)
        else:
            # Fallback for old local config if env vars are missing
            conn = psycopg2.connect(
                host=os.environ.get("DB_HOST", "localhost"),
                dbname=os.environ.get("DB_NAME", "csconnect"),
                user=os.environ.get("DB_USER", "postgres"),
                password=os.environ.get("DB_PASS", "1234"),
                port=os.environ.get("DB_PORT", "5432")
            )
        return conn
    except psycopg2.Error as e:
        print(f"Error connecting to the database: {e}")
        return None

def setup_unstructured_tables():
    """
    Creates the 'website_content' and 'document_chunks' tables if they don't exist.
    """
    create_website_content_sql = """
    CREATE TABLE IF NOT EXISTS website_content (
        id SERIAL PRIMARY KEY,
        url TEXT UNIQUE NOT NULL,
        title TEXT,
        content TEXT NOT NULL,
        scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """

    create_document_chunks_sql = """
    CREATE TABLE IF NOT EXISTS document_chunks (
        id SERIAL PRIMARY KEY,
        document_name TEXT NOT NULL,
        chunk_index INTEGER NOT NULL,
        content TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(document_name, chunk_index)
    );
    """

    conn = get_db_connection()
    if conn is None:
        return False

    try:
        with conn.cursor() as cur:
            cur.execute(create_website_content_sql)
            cur.execute(create_document_chunks_sql)
            conn.commit()
            print("Successfully initialized unstructured data tables.")
            return True
    except psycopg2.Error as e:
        print(f"Error creating unstructured tables: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def get_schema_summary() -> Dict[str, List[str]]:
    """
    Fetches a summary of all existing tables and their columns in the database.
    Useful for providing context to the AI chatbot.
    """
    schema_summary: Dict[str, List[str]] = {}
    conn = get_db_connection()
    if conn is None:
        return schema_summary

    query = """
    SELECT 
        table_name, 
        column_name, 
        data_type 
    FROM 
        information_schema.columns 
    WHERE 
        table_schema = 'public' 
    ORDER BY 
        table_name, ordinal_position;
    """

    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query)
            rows = cur.fetchall()
            
            for row in rows:
                table = str(row['table_name'])
                col = str(row['column_name'])
                dtype = str(row['data_type'])
                
                if table not in schema_summary:
                    schema_summary[table] = []
                
                schema_summary[table].append(f"{col} ({dtype})")
                
    except psycopg2.Error as e:
        print(f"Error fetching schema summary: {e}")
    finally:
        conn.close()

    return schema_summary

if __name__ == "__main__":
    # Test the connection and setup tables when run directly
    print("Testing database connection and setting up tables...")
    success = setup_unstructured_tables()
    
    if success:
        print("\nFetching schema summary for validation:")
        schema = get_schema_summary()
        
        if schema:
            # Print a sample of the schema to verify it works
            for i, table in enumerate(schema):
                if i >= 3:
                    break
                columns = schema[table]
                print(f"- Table: {table}")
                # Print only first 3 columns
                col_sample = []
                for j, col in enumerate(columns):
                    if j >= 3:
                        break
                    col_sample.append(col)
                
                print(f"  Columns: {', '.join(col_sample)}{'...' if len(columns) > 3 else ''}")
            print(f"... and {max(0, len(schema) - 3)} more tables.")
        else:
            print("Failed to fetch schema summary.")
