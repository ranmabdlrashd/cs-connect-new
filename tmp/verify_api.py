import os
import sys
import json
from api import get_student_dashboard_data, get_student_attendance_data, get_all_notes_data, get_faculty_list_data, api_bp

def verify():
    print("--- VERIFYING API IMPLEMENTATION ---")
    
    # 1. Check Blueprint
    print(f"API Blueprint Name: {api_bp.name}")
    print(f"API Blueprint URL Prefix: {api_bp.url_prefix}")
    
    # 2. Test DB Helpers
    # We need a valid user_id to test. Let's find one.
    from database import get_db_connection
    with get_db_connection() as conn:
        user = conn.execute("SELECT user_id FROM users LIMIT 1").fetchone()
        if user:
            user_id = user['user_id']
            print(f"Testing with user_id: {user_id}")
            
            # Dashboard
            dash_data = get_student_dashboard_data(user_id)
            print(f"Student Dashboard Data: {dash_data is not None}")
            if dash_data:
                print(f"  Attendance: {dash_data.get('attendance')}")
                print(f"  CGPA: {dash_data.get('cgpa')}")
                print(f"  Subjects Count: {len(dash_data.get('subjects', []))}")
            
            # Attendance
            att_data = get_student_attendance_data(user_id)
            print(f"Student Attendance Data (subjects): {len(att_data)}")
        else:
            print("No users found to test.")

    # 3. Notes
    try:
        notes = get_all_notes_data()
        print(f"All Notes Count: {len(notes)}")
    except Exception as e:
        print(f"Error fetching notes: {e}")

    # 4. Faculty
    try:
        faculty = get_faculty_list_data()
        print(f"Faculty Count: {len(faculty)}")
    except Exception as e:
        print(f"Error fetching faculty: {e}")

    print("--- VERIFICATION COMPLETE ---")

if __name__ == "__main__":
    verify()
