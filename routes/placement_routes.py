from flask import Blueprint, render_template, request, session, redirect, url_for, flash, jsonify
from models.placement import Placement

placement_bp = Blueprint("placement_bp", __name__)

@placement_bp.route('/dashboard/placements')
def student_placements():
    if not session.get("user_id"):
        return redirect(url_for("login"))
    if session.get("role") != "student":
        flash("Access denied.", "danger")
        return redirect(url_for("home"))
    return render_template("student_placement_portal.html")

@placement_bp.route('/api/placements/active')
def api_placements_active():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401
    
    try:
        user = Placement.get_user_profile(user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404
            
        user_cgpa = float(user['cgpa']) if user['cgpa'] else 0.0
        user_branch = user['branch'] or 'CSE'
        user_batch = (user['batch'] or '2026').strip()
        
        drives = Placement.get_active_drives(user_cgpa, user_branch, user_batch)
        applied_ids = Placement.get_applied_drive_ids(user_id)
        
        for d in drives:
            d['is_applied'] = d['id'] in applied_ids
            # Fix lint errors by checking type or casting
            if hasattr(d['drive_date'], 'strftime'):
                d['drive_date'] = d['drive_date'].strftime("%b %d, %Y")
            else:
                d['drive_date'] = str(d['drive_date'])
            
            try:
                d['min_cgpa'] = float(d['min_cgpa'])
            except (TypeError, ValueError):
                d['min_cgpa'] = 0.0
            
        return jsonify(drives)
    except Exception as e:
        print(f"Error in api_placements_active: {e}")
        return jsonify({"error": str(e)}), 500

@placement_bp.route('/api/placements/<int:drive_id>/apply', methods=['POST'])
def api_placements_apply(drive_id):
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401
        
    data = request.get_json() or {}
    try:
        # Check if already applied
        applied_ids = Placement.get_applied_drive_ids(user_id)
        if drive_id in applied_ids:
            return jsonify({"error": "Already applied"}), 400
            
        drive = Placement.get_drive_by_id(drive_id)
        user = Placement.get_user_profile(user_id)
        
        is_eligible = True
        if user and drive:
            if float(user['cgpa'] or 0) < float(drive['min_cgpa']): is_eligible = False
            
        if not is_eligible:
            return jsonify({"error": "Not eligible"}), 400
            
        Placement.apply(drive_id, user_id, data)
        return jsonify({"status": "success"})
    except Exception as e:
        print(f"Error in api_placements_apply: {e}")
        return jsonify({"error": str(e)}), 500

@placement_bp.route('/api/placements/my-applications')
def api_placements_my_applications():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401
        
    try:
        apps = Placement.get_user_applications(user_id)
        for a in apps:
            if hasattr(a['applied_date'], 'strftime'):
                a['applied_date'] = a['applied_date'].strftime("%b %d, %Y")
            else:
                a['applied_date'] = str(a['applied_date'])
        return jsonify(apps)
    except Exception as e:
        print(f"Error in api_placements_my_applications: {e}")
        return jsonify({"error": str(e)}), 500

@placement_bp.route('/api/placements/eligibility-summary')
def api_placements_eligibility_summary():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401
        
    try:
        user = Placement.get_user_profile(user_id)
        attendance = Placement.get_average_attendance(user_id)
        
        eligibility_count = 0
        if user:
            user_cgpa = float(user['cgpa'] or 0)
            user_branch = user['branch'] or 'CSE'
            user_batch = (user['batch'] or '2026').strip()
            
            # Use model to get active drives and count eligible ones
            drives = Placement.get_active_drives(user_cgpa, user_branch, user_batch)
            eligibility_count = sum(1 for d in drives if d.get('status') == 'open' and d.get('is_eligible'))
            
        return jsonify({
            "cgpa": float(user['cgpa']) if user and user['cgpa'] else 0.0,
            "branch": user['branch'] if user else "CSE",
            "batch": user['batch'] if user else "2026",
            "backlogs": 0,
            "attendance": attendance,
            "eligible_drives_count": eligibility_count
        })
    except Exception as e:
        print(f"Error in api_placements_eligibility_summary: {e}")
        return jsonify({"error": str(e)}), 500
