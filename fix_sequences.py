import psycopg2
import logging
from dotenv import load_dotenv
import os

load_dotenv()

# Setup module-level logger
logger = logging.getLogger(__name__)

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_NAME = os.getenv("DB_NAME", "csconnect")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASS = os.getenv("DB_PASS", "postgres")

def fix_sequences():
    try:
        conn = psycopg2.connect(host=DB_HOST, dbname=DB_NAME, user=DB_USER, password=DB_PASS)
        cursor = conn.cursor()
    except Exception:
        logger.exception("Failed to connect to database in fix_sequences")
        return

    tables = [
        "users", "faculty", "books", "programs", "semesters", "news_ticker", 
        "alumni", "internships", "placement_companies", "placement_summary",
        "issues", "requests", "notifications"
    ]
    
    try:
        for table in tables:
            # Check if table exists
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' AND table_name = %s
                );
            """, (table,))
            exists = cursor.fetchone()[0]
            
            if exists:
                try:
                    cursor.execute(f"SELECT setval(pg_get_serial_sequence('{table}', 'id'), coalesce(max(id), 1), max(id) IS NOT null) FROM {table};")
                    logger.info("Fixed sequence for table: %s", table)
                except Exception:
                    logger.warning("Could not fix sequence for table %s (might not have 'id' column or serial)", table)
                
        conn.commit()
        logger.info("All sequences fixed successfully.")
    except Exception:
        logger.exception("Error during sequence fix process")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    fix_sequences()
