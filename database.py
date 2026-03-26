import os
import logging
import time
import functools
from typing import Dict, List, Any, Callable
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Setup structured logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)

class DatabaseError(Exception):
    """Custom exception for database-related errors."""
    pass

class ConnectionWrapper:
    """
    A wrapper around psycopg2 connection to provide convenience methods
    like execute, commit, and ensure proper cursor handling.
    """
    def __init__(self, conn):
        self.conn = conn

    def cursor(self, cursor_factory=None):
        if cursor_factory is None:
            # Default to DictCursor if possible, or use the one provided
            try:
                from psycopg2.extras import DictCursor
                cursor_factory = DictCursor
            except ImportError:
                pass
        return self.conn.cursor(cursor_factory=cursor_factory)

    def execute(self, query, params=None):
        """Execute a query and return the cursor."""
        from psycopg2.extras import DictCursor
        cur = self.conn.cursor(cursor_factory=DictCursor)
        if params:
            cur.execute(query, params)
        else:
            cur.execute(query)
        return cur

    def commit(self):
        self.conn.commit()

    def rollback(self):
        self.conn.rollback()

    def close(self):
        self.conn.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

def get_db_connection():
    """
    Establish and return a connection to the PostgreSQL database with retries.
    NEVER returns None. Raises DatabaseError if all attempts fail.
    """
    urls = [
        os.environ.get("NEON_DATABASE_URL"),
        os.environ.get("LOCAL_DATABASE_URL"),
        os.environ.get("DATABASE_URL")
    ]
    urls = [u for u in urls if u]
    max_retries = 3

    for db_url in urls:
        # Mask credentials for logging
        display_url = db_url.split('@')[-1] if '@' in db_url else "configured_url"
        for attempt in range(max_retries):
            try:
                logger.info("Connecting to DB (Attempt %d/%d) - Target: %s", attempt + 1, max_retries, display_url)
                conn = psycopg2.connect(db_url, connect_timeout=5)
                logger.info("Database connection successful")
                return ConnectionWrapper(conn)
            except Exception:
                logger.warning("Retry %d failed for database connection", attempt + 1)
                if attempt == max_retries - 1:
                    logger.exception("Persistent connection failure for URL: %s", display_url)
                else:
                    time.sleep(1)

    raise DatabaseError("All database connection attempts failed across all configured URLs.")


def with_db_connection(func: Callable):
    """
    Decorator that provides a database connection to the wrapped function.
    Handles connection creation, closing, and error logging.
    The wrapped function should accept 'conn' as its first argument.
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        conn = None
        try:
            conn = get_db_connection()
            return func(conn, *args, **kwargs)
        except DatabaseError as e:
            logger.error(f"Database error in {func.__name__}: {e}")
            raise # Re-raise to be handled by controller if needed
        except Exception as e:
            logger.error(f"Unexpected error in {func.__name__}: {e}")
            raise
        finally:
            if conn:
                conn.close()
                logger.debug(f"Database connection closed for {func.__name__}")
    return wrapper


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

    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute(create_website_content_sql)
            cur.execute(create_document_chunks_sql)
            conn.commit()
            logger.info("Successfully initialized unstructured data tables.")
            return True
    except (psycopg2.Error, DatabaseError) as e:
        logger.error(f"Error creating unstructured tables: {e}")
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            conn.close()


def get_schema_summary() -> Dict[str, List[str]]:
    """
    Fetches a summary of all existing tables and their columns in the database.
    Useful for providing context to the AI chatbot.
    """
    schema_summary: Dict[str, List[str]] = {}
    conn = None
    
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
        conn = get_db_connection()
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
                
    except (psycopg2.Error, DatabaseError) as e:
        logger.error(f"Error fetching schema summary: {e}")
    finally:
        if conn:
            conn.close()

    return schema_summary


if __name__ == "__main__":
    # Test the connection and setup tables when run directly
    logger.info("Testing database connection and setting up tables...")
    success = setup_unstructured_tables()
    
    if success:
        logger.info("Fetching schema summary for validation:")
        schema = get_schema_summary()
        
        if schema:
            # Log a sample of the schema to verify it works
            for i, table in enumerate(schema):
                if i >= 3:
                    break
                columns = schema[table]
                logger.info("- Table: %s", table)
                # Log only first 3 columns
                col_sample = []
                for j, col in enumerate(columns):
                    if j >= 3:
                        break
                    col_sample.append(col)
                
                logger.info("  Columns: %s%s", ', '.join(col_sample), '...' if len(columns) > 3 else '')
            logger.info("... and %d more tables.", max(0, len(schema) - 3))
        else:
            logger.error("Failed to fetch schema summary.")
