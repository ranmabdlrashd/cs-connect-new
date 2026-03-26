import os
import psycopg2
import sys
import logging
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

# Setup module-level logger
logger = logging.getLogger(__name__)

# Force UTF-8 encoding for Windows console if needed for stdout fallback
if sys.platform == "win32":
    import codecs
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())

load_dotenv()

def inspect_site_data():
    db_url = os.environ.get("NEON_DATABASE_URL")
    if not db_url:
        logger.error("NEON_DATABASE_URL not found in .env")
        return

    try:
        conn = psycopg2.connect(db_url)
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT key, data FROM site_data;")
            rows = cur.fetchall()
            
            if not rows:
                logger.info("The site_data table is empty.")
            else:
                logger.info("Found %d records in site_data:", len(rows))
                for row in rows:
                    key = row['key']
                    data_str = str(row['data'])
                    preview = data_str[:200] + "..." if len(data_str) > 200 else data_str
                    logger.info("Key: %s", key)
                    logger.info("Data Preview: %s", preview)
        conn.close()
    except Exception:
        logger.exception("Error during database inspection")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    inspect_site_data()
