import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def migrate():
    db_url = os.environ.get("NEON_DATABASE_URL") or os.environ.get("LOCAL_DATABASE_URL") or os.environ.get("DATABASE_URL")
    conn = psycopg2.connect(db_url)
    cur = conn.cursor()

    try:
        tables_to_rename_id = [
            "users", "books", "faculty", "placement_summary", "placement_companies", "alumni",
            "internships", "programs", "semesters", "news_ticker", "home_stats",
            "placement_batches", "timetable_subjects", "timetable", "mous",
            "internal_marks", "placement_drives", "placement_applications",
            "notices", "faculty_feedback", "marks_register"
        ]

        for table in tables_to_rename_id:
            print(f"Checking {table} for id rename...")
            try:
                # Check if column 'id' exists
                cur.execute(f"""
                    SELECT count(*) FROM information_schema.columns 
                    WHERE table_name='{table}' AND column_name='id'
                """)
                if cur.fetchone()[0] > 0:
                    cur.execute(f"ALTER TABLE {table} RENAME COLUMN id TO sl_no")
                    print(f"Renamed {table}(id) -> {table}(sl_no)")
                else:
                    print(f"Column 'id' not found in {table}. Skipping.")
                conn.commit()
            except Exception as e:
                print(f"Error checking/renaming {table}: {e}")
                conn.rollback()

        # Specific check for users primary key
        print("Ensuring users table has user_id as primary key...")
        try:
            cur.execute("ALTER TABLE users DROP CONSTRAINT IF EXISTS users_pkey CASCADE")
            cur.execute("ALTER TABLE users ALTER COLUMN user_id SET NOT NULL")
            cur.execute("""
                SELECT count(*) FROM information_schema.table_constraints 
                WHERE table_name='users' AND constraint_type='PRIMARY KEY'
            """)
            if cur.fetchone()[0] == 0:
                cur.execute("ALTER TABLE users ADD PRIMARY KEY (user_id)")
            conn.commit()
        except Exception as e:
            print(f"Error updating users PK: {e}")
            conn.rollback()

        print("Dropping dependent tables...")
        tables_to_drop = [
            "results", "issues", "requests", "notifications", "library_fines", 
            "book_reservations", "resource_downloads", "attendance", "download_logs"
        ]
        for table in tables_to_drop:
            cur.execute(f"DROP TABLE IF EXISTS {table} CASCADE")

        print("Recreating dependent tables with TEXT foreign keys and sl_no...")
        
        # 1. Results
        cur.execute("""
        CREATE TABLE results (
            sl_no SERIAL PRIMARY KEY,
            student_id TEXT REFERENCES users(user_id) ON DELETE CASCADE,
            subject_code TEXT,
            internal_marks INTEGER,
            attendance_pct INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        # 2. Issues (Library)
        cur.execute("""
        CREATE TABLE issues (
            sl_no SERIAL PRIMARY KEY,
            book_id INTEGER,
            user_id TEXT REFERENCES users(user_id) ON DELETE CASCADE,
            issue_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            due_date TIMESTAMP,
            return_date TIMESTAMP,
            status TEXT DEFAULT 'issued'
        )
        """)

        # 3. Requests (Library)
        cur.execute("""
        CREATE TABLE requests (
            sl_no SERIAL PRIMARY KEY,
            book_id INTEGER,
            requested_by TEXT REFERENCES users(user_id) ON DELETE CASCADE,
            request_type TEXT,
            status TEXT DEFAULT 'pending',
            request_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            admin_feedback TEXT
        )
        """)

        # 4. Notifications
        cur.execute("""
        CREATE TABLE notifications (
            sl_no SERIAL PRIMARY KEY,
            user_id TEXT REFERENCES users(user_id) ON DELETE CASCADE,
            title TEXT,
            body TEXT,
            category TEXT,
            is_read BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # 5. Library Fines
        cur.execute("""
        CREATE TABLE library_fines (
            sl_no SERIAL PRIMARY KEY,
            student_id TEXT REFERENCES users(user_id) ON DELETE CASCADE,
            loan_id INTEGER,
            amount DECIMAL(10,2),
            reason TEXT,
            paid BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        # 6. Book Reservations
        cur.execute("""
        CREATE TABLE book_reservations (
            sl_no SERIAL PRIMARY KEY,
            student_id TEXT REFERENCES users(user_id) ON DELETE CASCADE,
            book_id INTEGER,
            status TEXT DEFAULT 'waiting',
            queue_position INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        # 7. Resource Downloads
        cur.execute("""
        CREATE TABLE resource_downloads (
            sl_no SERIAL PRIMARY KEY,
            resource_id INTEGER,
            user_id TEXT REFERENCES users(user_id) ON DELETE CASCADE,
            downloaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        conn.commit()
        print("Migration successful: Project-wide sl_no renaming completed.")

    except Exception as e:
        print(f"Critical error during migration: {e}")
        conn.rollback()
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    migrate()
