from flask import Blueprint, jsonify, request, session
from database import db_connection
import json
import logging

# LOGGING SETUP
logger = logging.getLogger(__name__)

api_bp = Blueprint("api", __name__, url_prefix="/api")

# --- DATABASE HELPER FUNCTIONS ---

def get_student_dashboard_data(user_id):
    """
    Fetches student performance data and enrolled subjects from the database.
    Does NOT contain raw SQL inside the route.
    """
    with db_connection() as conn:
        # Get the internal primary key (sl_no) for the given user_id (roll_no)
        user = conn.execute("SELECT sl_no FROM users WHERE user_id = %s", (user_id,)).fetchone()
        if not user:
            return None
        
        user_sl_no = user['sl_no']
        
        # 1. Fetch performance stats (cgpa, attendance)
        perf = conn.execute("""
            SELECT cgpa, attendance_pct 
            FROM student_performance 
            WHERE user_id = %s
        """, (user_sl_no,)).fetchone()
        
        # 2. Fetch subject names from internal marks
        subjects_rows = conn.execute("""
            SELECT subject_name FROM internal_marks 
            WHERE user_id = %s
        """, (user_sl_no,)).fetchall()
        
        subjects = [row['subject_name'] for row in subjects_rows]
        
        return {
            "attendance": float(perf['attendance_pct']) if perf else 0.0,
            "cgpa": float(perf['cgpa']) if perf else 0.0,
            "subjects": subjects
        }

def get_student_attendance_data(user_id):
    """
    Fetches subject-wise attendance percentages for a specific student.
    """
    with db_connection() as conn:
        user = conn.execute("SELECT sl_no FROM users WHERE user_id = %s", (user_id,)).fetchone()
        if not user:
            return []
        
        user_sl_no = user['sl_no']
        
        rows = conn.execute("""
            SELECT subject_name, attendance 
            FROM internal_marks 
            WHERE user_id = %s
        """, (user_sl_no,)).fetchall()
        
        return [{"name": row['subject_name'], "attendance": float(row['attendance'] or 0)} for row in rows]

def get_all_notes_data():
    """
    Retrieves all available study materials/notes from the semesters subjects catalog.
    """
    with db_connection() as conn:
        rows = conn.execute("SELECT subjects FROM semesters").fetchall()
        all_notes = []
        for row in rows:
            subjects = json.loads(row['subjects']) if isinstance(row['subjects'], str) else row['subjects']
            if not subjects: continue
            
            for subj in subjects:
                if 'notes' in subj and isinstance(subj['notes'], dict):
                    for module, url in subj['notes'].items():
                        all_notes.append({
                            "subject": subj.get('name', 'General'),
                            "file": f"{subj.get('code', 'NOTE')}_{module.replace(' ', '_')}.pdf",
                            "url": url
                        })
        return all_notes

def get_faculty_list_data():
    """
    Fetches a list of faculty members with their research interests and contact emails.
    """
    with db_connection() as conn:
        rows = conn.execute("SELECT sl_no, name, designation, designation_key, qualification, research, email, photo FROM faculty ORDER BY sl_no ASC").fetchall()
        return [dict(row) for row in rows]


# --- REST API ENDPOINTS ---

@api_bp.route("/student/dashboard", methods=["GET"])
def student_dashboard():
    """
    GET /api/student/dashboard
    Returns summary data for the student dashboard.
    """
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({"success": False, "error": "Unauthorized"}), 401
            
        data = get_student_dashboard_data(user_id)
        if not data:
            return jsonify({"success": False, "error": "Student profile not found"}), 404
            
        return jsonify({"success": True, "data": data})
    except Exception as e:
        logger.error(f"API Error [/student/dashboard]: {str(e)}")
        return jsonify({"success": False, "error": "Internal server error"}), 500


@api_bp.route("/student/attendance", methods=["GET"])
def student_attendance():
    """
    GET /api/student/attendance
    Returns detailed subject-wise attendance.
    """
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({"success": False, "error": "Unauthorized"}), 401
            
        subjects = get_student_attendance_data(user_id)
        return jsonify({"success": True, "data": {"subjects": subjects}})
    except Exception as e:
        logger.error(f"API Error [/student/attendance]: {str(e)}")
        return jsonify({"success": False, "error": "Internal server error"}), 500


@api_bp.route("/notes", methods=["GET"])
def get_notes():
    """
    GET /api/notes
    Returns a list of all available notes.
    """
    try:
        notes = get_all_notes_data()
        return jsonify({"success": True, "data": {"notes": notes}})
    except Exception as e:
        logger.error(f"API Error [/notes]: {str(e)}")
        return jsonify({"success": False, "error": "Internal server error"}), 500


@api_bp.route("/faculty", methods=["GET"])
def get_faculty():
    """
    GET /api/faculty
    Returns a list of faculty members.
    """
    try:
        faculty = get_faculty_list_data()
        return jsonify({"success": True, "data": faculty})
    except Exception as e:
        logger.error(f"API Error [/faculty]: {str(e)}")
        return jsonify({"success": False, "error": "Internal server error"}), 500
