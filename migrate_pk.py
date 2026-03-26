import os
import psycopg2
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("migration.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def get_db_connection():
    """Establishes a connection to the database using environment variables."""
    db_url = os.environ.get("NEON_DATABASE_URL") or os.environ.get("LOCAL_DATABASE_URL") or os.environ.get("DATABASE_URL")
    if not db_url:
        raise ValueError("Database URL not found in environment variables.")
    return psycopg2.connect(db_url)

def get_foreign_keys_referencing(cur, table_name, column_name):
    """Finds all foreign keys in the database that reference table_name(column_name)."""
    # Using pg_constraint for more robust lookup in Postgres
    query = """
        SELECT
            conrelid::regclass::text as table_name,
            a.attname as column_name,
            conname as constraint_name
        FROM
            pg_constraint AS c
            JOIN pg_attribute AS a ON a.attrelid = c.conrelid AND a.attnum = ANY(c.conkey)
            JOIN pg_attribute AS af ON af.attrelid = c.confrelid AND af.attnum = ANY(c.confkey)
        WHERE
            c.contype = 'f'
            AND confrelid = %s::regclass
            AND af.attname = %s;
    """
    cur.execute(query, (table_name, column_name))
    return cur.fetchall()

def safe_migrate_table(cur, table_name):
    """Performs a safe, production-ready migration of the ID column to sl_no."""
    logger.info(f">>> Processing table: {table_name}")
    
    # 1. Backup table (Safety)
    backup_name = f"{table_name}_backup"
    try:
        cur.execute(f"DROP TABLE IF EXISTS {backup_name}")
        cur.execute(f"CREATE TABLE {backup_name} AS SELECT * FROM {table_name}")
        logger.info(f"Backup created: {backup_name}")
    except Exception as e:
        logger.error(f"Failed to create backup for {table_name}: {e}")
        raise

    # 2. Check for 'id' column
    cur.execute("""
        SELECT count(*) FROM information_schema.columns 
        WHERE table_name=%s AND column_name='id'
    """, (table_name,))
    if cur.fetchone()[0] == 0:
        logger.warning(f"Column 'id' not found in {table_name}. Skipping safe migration.")
        return

    # 3. Add 'sl_no' column if it doesn't exist
    cur.execute("""
        SELECT count(*) FROM information_schema.columns 
        WHERE table_name=%s AND column_name='sl_no'
    """, (table_name,))
    if cur.fetchone()[0] == 0:
        cur.execute(f"ALTER TABLE {table_name} ADD COLUMN sl_no SERIAL")
        logger.info(f"Added column 'sl_no' (SERIAL) to {table_name}")
    else:
        logger.info(f"Column 'sl_no' already exists in {table_name}")

    # 4. Copy data safely (Preserve existing IDs)
    cur.execute(f"UPDATE {table_name} SET sl_no = id")
    logger.info(f"Synchronized sl_no with id values in {table_name}")

    # 5. Find Foreign Keys referencing the OLD id (Snapshot them before CASCADE drop)
    fks = get_foreign_keys_referencing(cur, table_name, 'id')
    logger.info(f"Found {len(fks)} foreign keys to preserve for {table_name}")

    # 6. Handle Primary Key Constraints
    # Identify existing UK/PK constraint name
    cur.execute("""
        SELECT constraint_name 
        FROM information_schema.table_constraints 
        WHERE table_name=%s AND constraint_type='PRIMARY KEY'
    """, (table_name,))
    pk_row = cur.fetchone()
    if pk_row:
        old_pk_name = pk_row[0]
        # CASCADE will drop referencing foreign keys automatically
        cur.execute(f"ALTER TABLE {table_name} DROP CONSTRAINT {old_pk_name} CASCADE")
        logger.info(f"Dropped old PK constraint (CASCADE): {old_pk_name}")
    
    # Set the new primary key on sl_no
    cur.execute(f"ALTER TABLE {table_name} ADD PRIMARY KEY (sl_no)")
    logger.info(f"New Primary Key set on {table_name}(sl_no)")

    # 7. Recreate Foreign Keys pointing to sl_no
    for fk_table, fk_column, constraint_name in fks:
        logger.info(f"Recreating FK {constraint_name} on {fk_table}.{fk_column} to reference {table_name}.sl_no")
        # Ensure it's dropped (it might have been dropped by CASCADE, but safety first)
        cur.execute(f"ALTER TABLE {fk_table} DROP CONSTRAINT IF EXISTS {constraint_name}")
        cur.execute(f"ALTER TABLE {fk_table} ADD CONSTRAINT {constraint_name} FOREIGN KEY ({fk_column}) REFERENCES {table_name}(sl_no)")

    # 7. Validation
    # Row counts
    cur.execute(f"SELECT count(*) FROM {table_name}")
    actual_count = cur.fetchone()[0]
    cur.execute(f"SELECT count(*) FROM {backup_name}")
    backup_count = cur.fetchone()[0]
    
    if actual_count != backup_count:
        raise ValueError(f"COUNT MISMATCH: {table_name} has {actual_count} rows, vs backup {backup_count}")
    
    # Uniqueness
    cur.execute(f"SELECT count(DISTINCT sl_no) FROM {table_name}")
    unique_count = cur.fetchone()[0]
    if unique_count != actual_count:
        raise ValueError(f"UNIQUENESS VIOLATION: sl_no in {table_name} contains duplicates")

    logger.info(f"Successful migration for: {table_name}")

def rollback_migration(cur, table_name):
    """Reverts the migration for a specific table using its backup."""
    logger.warning(f"!!! Rolling back table: {table_name}")
    backup_name = f"{table_name}_backup"
    
    # 1. Check if backup exists
    cur.execute("SELECT count(*) FROM information_schema.tables WHERE table_name=%s", (backup_name,))
    if cur.fetchone()[0] == 0:
        logger.error(f"Rollback failed: Backup {backup_name} does not exist.")
        return

    try:
        # 0. Find FKs referencing 'sl_no' before we drop the PK
        fks_new = get_foreign_keys_referencing(cur, table_name, 'sl_no')
        logger.info(f"Found {len(fks_new)} foreign keys to restore to 'id' for {table_name}")

        # 1. Drop the sl_no PK (CASCADE to be safe, though we'll recreate FKs)
        # We need to find the current PK name first
        cur.execute("""
            SELECT constraint_name 
            FROM information_schema.table_constraints 
            WHERE table_name=%s AND constraint_type='PRIMARY KEY'
        """, (table_name,))
        pk_row = cur.fetchone()
        if pk_row:
            cur.execute(f"ALTER TABLE {table_name} DROP CONSTRAINT {pk_row[0]} CASCADE")
            logger.info(f"Dropped sl_no PK constraint: {pk_row[0]}")

        # 2. Restore PK to 'id'
        cur.execute(f"ALTER TABLE {table_name} ADD PRIMARY KEY (id)")
        logger.info(f"Restored Primary Key to {table_name}(id)")
        
        # 3. Reset FKs pointing to sl_no back to id
        for fk_table, fk_column, constraint_name in fks_new:
            logger.info(f"Restoring FK {constraint_name} on {fk_table}.{fk_column} to reference {table_name}.id")
            cur.execute(f"ALTER TABLE {fk_table} DROP CONSTRAINT IF EXISTS {constraint_name}")
            cur.execute(f"ALTER TABLE {fk_table} ADD CONSTRAINT {constraint_name} FOREIGN KEY ({fk_column}) REFERENCES {table_name}(id)")
            
        # 4. Drop sl_no column
        cur.execute(f"ALTER TABLE {table_name} DROP COLUMN IF EXISTS sl_no")
        
        logger.info(f"Rollback complete for {table_name}")
    except Exception as e:
        logger.error(f"Critical error during rollback of {table_name}: {e}")
        raise

def main(mode='migrate'):
    tables = [
        "users", "books", "faculty", "placement_summary", "placement_companies", "alumni",
        "internships", "programs", "semesters", "news_ticker", "home_stats",
        "placement_batches", "timetable_subjects", "timetable", "mous",
        "internal_marks", "placement_drives", "placement_applications",
        "notices", "faculty_feedback", "marks_register",
        "results", "issues", "requests", "notifications", "library_fines", 
        "book_reservations", "resource_downloads", "attendance", "download_logs"
    ]

    conn = None
    try:
        conn = get_db_connection()
        # Ensure we are in transaction mode
        conn.autocommit = False
        cur = conn.cursor()

        for table in tables:
            # Check if table exists
            cur.execute("SELECT count(*) FROM information_schema.tables WHERE table_name=%s", (table,))
            if cur.fetchone()[0] == 0:
                logger.debug(f"Table {table} not found in database. Skipping.")
                continue

            try:
                if mode == 'migrate':
                    safe_migrate_table(cur, table)
                else:
                    rollback_migration(cur, table)
                
                # Commit per table to avoid long-running lock on entire DB
                conn.commit()
                logger.debug(f"Transaction committed for {table}")
            except Exception as e:
                conn.rollback()
                logger.error(f"Transaction ROLLED BACK for {table} due to error: {e}")
                # We stop on error to prevent inconsistent state
                logger.critical("Stopping migration due to failure.")
                break

    except Exception as e:
        logger.critical(f"Database connection or fatal error: {e}")
    finally:
        if conn:
            conn.close()
            logger.info("Database connection closed.")

if __name__ == "__main__":
    import sys
    mode = 'migrate'
    if len(sys.argv) > 1 and sys.argv[1].lower() == 'rollback':
        mode = 'rollback'
        logger.warning("RUNNING IN ROLLBACK MODE")
    
    main(mode)
