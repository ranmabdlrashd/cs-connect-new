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

def drop_shelf():
    try:
        conn = psycopg2.connect(host=DB_HOST, dbname=DB_NAME, user=DB_USER, password=DB_PASS)
        cursor = conn.cursor()
    except Exception:
        logger.exception("Failed to connect to database in drop_shelf")
        return

    try:
        cursor.execute("ALTER TABLE books DROP COLUMN IF EXISTS shelf")
        cursor.execute("ALTER TABLE books DROP COLUMN IF EXISTS shelf_location")
        conn.commit()
        logger.info("Shelf columns dropped successfully.")
    except Exception:
        logger.exception("Error dropping shelf columns")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    drop_shelf()
