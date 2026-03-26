import os
import json
import psycopg2
from dotenv import load_dotenv

load_dotenv()

from database import db_connection

def seed():
    with db_connection() as conn:
        cur = conn.cursor()
    
    print("Checking essential records in site_data...")
    
    # Check for 'placement_team'
    cur.execute("SELECT * FROM site_data WHERE key = 'placement_team'")
    if not cur.fetchone():
        print("Inserting default 'placement_team'...")
        team_data = {
            "faculty_coordinator": {
                "name": "Prof. TBD",
                "designation": "Placement Coordinator",
                "email": "faculty@example.com",
                "photo": "https://via.placeholder.com/150"
            },
            "student_coordinators": [
                {
                    "name": "Student A",
                    "email": "studenta@example.com"
                },
                {
                    "name": "Student B",
                    "email": "studentb@example.com"
                }
            ]
        }
        cur.execute(
            "INSERT INTO site_data (key, data) VALUES (%s, %s)",
            ('placement_team', json.dumps(team_data))
        )
    else:
        print("'placement_team' already exists.")

    # Check for 'home_stats' (basic site configuration example)
    cur.execute("SELECT * FROM site_data WHERE key = 'home_stats'")
    if not cur.fetchone():
        print("Inserting default 'home_stats'...")
        stats_data = [
            {"value": "100+", "label": "Students"},
            {"value": "20+", "label": "Faculty"}
        ]
        cur.execute(
            "INSERT INTO site_data (key, data) VALUES (%s, %s)",
            ('home_stats', json.dumps(stats_data))
        )
    else:
        print("'home_stats' already exists.")

        conn.commit()
    print("Database seeding completed.")

if __name__ == "__main__":
    try:
        seed()
    except Exception as e:
        print(f"Error during seeding: {e}")
