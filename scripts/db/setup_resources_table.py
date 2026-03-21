import os
import psycopg2
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def get_db_connection():
    db_url = os.environ.get("NEON_DATABASE_URL") or os.environ.get("LOCAL_DATABASE_URL") or os.environ.get("DATABASE_URL")
    
    try:
        if db_url:
            return psycopg2.connect(db_url)
        else:
            return psycopg2.connect(
                host=os.environ.get("DB_HOST", "localhost"),
                dbname=os.environ.get("DB_NAME", "csconnect"),
                user=os.environ.get("DB_USER", "postgres"),
                password=os.environ.get("DB_PASS", "1234"),
                port=os.environ.get("DB_PORT", "5432")
            )
    except psycopg2.Error as e:
        print(f"Error connecting to database: {e}")
        return None

def setup_resources_table():
    create_sql = """
    CREATE TABLE IF NOT EXISTS resources (
        id SERIAL PRIMARY KEY,
        title TEXT NOT NULL,
        description TEXT,
        file_url TEXT NOT NULL,
        file_size TEXT,
        category TEXT NOT NULL,
        semester INTEGER
    );
    """
    conn = get_db_connection()
    if not conn:
        print("Could not connect to database")
        return
    try:
        cur = conn.cursor()
        cur.execute(create_sql)
        
        # Check if empty, insert dummy data
        cur.execute("SELECT COUNT(*) FROM resources")
        if cur.fetchone()[0] == 0:
            print("Inserting dummy resources...")
            dummy_data = [
                # Semester 1
                ("B.Tech 2019 Scheme S1 Syllabus", "Complete syllabus for Semester 1", "#", "1.2 MB", "syllabus", 1),
                ("Physics Lab Manual S1", "Experiment guidelines and record format", "#", "540 KB", "lab_manual", 1),
                ("Mathematics Question Bank", "Previous year questions for MAT 101", "#", "800 KB", "question_bank", 1),
                ("S1 Physics University Paper 2022", "Past question paper", "#", "200 KB", "prev_papers", 1),
                
                # Semester 2
                ("B.Tech 2019 Scheme S2 Syllabus", "Complete syllabus for Semester 2", "#", "1.3 MB", "syllabus", 2),
                ("Programming in C Lab Manual", "C programs and exercises", "#", "600 KB", "lab_manual", 2),
                
                # Semester 4
                ("B.Tech 2019 Scheme S4 Syllabus", "Complete syllabus for Semester 4", "#", "1.4 MB", "syllabus", 4),
                
                # Semester 6
                ("B.Tech 2019 Scheme S6 Syllabus", "Complete syllabus for Semester 6", "#", "1.5 MB", "syllabus", 6),
                ("Compiler Design Notes", "Module 1-6 detailed notes", "#", "3.2 MB", "department_general", 6), # To test filtering
                
                # General Department Resources
                ("Full KTU B.Tech 2019 Scheme PDF", "Complete scheme combining S1 to S8", "#", "8.5 MB", "department_general", 0),
                ("KTU Academic Regulations 2019", "Rules and regulations B.Tech", "#", "2.1 MB", "department_general", 0),
                ("Academic Calendar 2025-26", "Dept dates, internal exams", "#", "150 KB", "department_general", 0)
            ]
            cur.executemany("INSERT INTO resources (title, description, file_url, file_size, category, semester) VALUES (%s, %s, %s, %s, %s, %s)", dummy_data)
        
        # Also create analytics table for downloads
        cur.execute("""
        CREATE TABLE IF NOT EXISTS resource_downloads (
            id SERIAL PRIMARY KEY,
            resource_id INTEGER,
            user_id INTEGER,
            downloaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)
        
        conn.commit()
        print("Resources table created/verified successfully.")
        
    except Exception as e:
        print(f"Error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == '__main__':
    setup_resources_table()
