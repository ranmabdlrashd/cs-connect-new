import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def setup_placements():
    db_url = os.environ.get("NEON_DATABASE_URL") or os.environ.get("LOCAL_DATABASE_URL") or os.environ.get("DATABASE_URL")
    if not db_url:
        print("No database URL found")
        return

    conn = psycopg2.connect(db_url)
    cur = conn.cursor()

    try:
        # 1. placement_drives table
        print("Creating placement_drives table...")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS placement_drives (
                id SERIAL PRIMARY KEY,
                company_name TEXT NOT NULL,
                role TEXT NOT NULL,
                package TEXT NOT NULL,
                drive_date DATE NOT NULL,
                location TEXT NOT NULL,
                status TEXT NOT NULL, -- 'open', 'upcoming', 'closed'
                min_cgpa NUMERIC(4,2) NOT NULL,
                eligible_branches TEXT NOT NULL, -- comma separated, e.g. 'CSE, ECE'
                eligible_batch TEXT NOT NULL, -- e.g. '2026'
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 2. placement_applications table
        print("Creating placement_applications table...")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS placement_applications (
                id SERIAL PRIMARY KEY,
                drive_id INTEGER REFERENCES placement_drives(id),
                student_id INTEGER NOT NULL, -- references users(id)
                applied_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT NOT NULL DEFAULT 'Applied', -- 'Applied', 'Shortlisted', 'Selected', 'Rejected'
                contact_number TEXT,
                cover_letter TEXT,
                resume_url TEXT,
                linkedin_url TEXT
            )
        """)

        # 3. results table (if not exists)
        print("Creating results table...")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS results (
                id SERIAL PRIMARY KEY,
                student_id INTEGER NOT NULL,
                cgpa NUMERIC(4,2),
                semester INTEGER,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Seed initial data for drives
        print("Seeding initial placement drives...")
        drives = [
            ('Google', 'Software Engineer', '₹32.5 LPA', '2026-05-15', 'Bangalore', 'open', 8.5, 'CSE, ECE', '2026'),
            ('Microsoft', 'SDE-1', '₹28 LPA', '2026-06-10', 'Hyderabad', 'upcoming', 8.0, 'CSE, IT', '2026'),
            ('TCS Ninja', 'Assistant Systems Engineer', '₹3.5 LPA', '2026-04-20', 'Kochi', 'closed', 6.0, 'All Branches', '2025'),
            ('Accenture', 'Associate Software Engineer', '₹4.5 LPA', '2026-07-01', 'Pune', 'upcoming', 6.5, 'CSE, IT, ECE', '2026'),
            ('Infosys', 'Specialist Programmer', '₹8 LPA', '2026-05-30', 'Mysuru', 'open', 7.5, 'CSE, IT', '2026')
        ]
        
        # Clear existing drives for fresh seed
        cur.execute("DELETE FROM placement_drives")
        cur.execute("ALTER SEQUENCE placement_drives_id_seq RESTART WITH 1")
        
        for drive in drives:
            cur.execute("""
                INSERT INTO placement_drives (company_name, role, package, drive_date, location, status, min_cgpa, eligible_branches, eligible_batch)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, drive)

        # Seed CGPA for students if not exists
        # Get student user IDs
        cur.execute("SELECT id FROM users WHERE role = 'student'")
        students = cur.fetchall()
        for s in students:
            # Check if has CGPA record
            cur.execute("SELECT id FROM results WHERE student_id = %s", (s[0],))
            if not cur.fetchone():
                import random
                cgpa = round(random.uniform(7.0, 9.5), 2)
                cur.execute("INSERT INTO results (student_id, cgpa, semester) VALUES (%s, %s, 6)", (s[0], cgpa))

        conn.commit()
        print("Database setup successfully!")
    except Exception as e:
        print(f"Error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    setup_placements()
