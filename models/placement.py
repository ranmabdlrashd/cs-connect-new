def get_db():
    from app import get_db_connection
    return get_db_connection()

class Placement:
    @staticmethod
    def get_user_profile(user_id):
        conn = get_db()
        user = conn.execute("SELECT u.branch, u.batch, r.cgpa FROM users u LEFT JOIN results r ON u.id = r.student_id WHERE u.id = %s", (user_id,)).fetchone()
        conn.close()
        return dict(user) if user else None

    @staticmethod
    def get_average_attendance(student_id):
        conn = get_db()
        att_row = conn.execute("SELECT AVG(percentage) FROM attendance WHERE student_id = %s", (student_id,)).fetchone()
        conn.close()
        return float(att_row[0]) if att_row and att_row[0] is not None else 0.0

    @staticmethod
    def get_active_drives(user_cgpa, user_branch, user_batch):
        conn = get_db()
        drives_cursor = conn.execute("""
            SELECT *, 
                   CASE 
                       WHEN %s >= min_cgpa 
                            AND (eligible_branches ILIKE '%%' || %s || '%%' OR eligible_branches = 'All Branches')
                            AND eligible_batch = %s
                       THEN true ELSE false 
                   END as is_eligible
            FROM placement_drives
            WHERE status IN ('open', 'upcoming')
            ORDER BY drive_date ASC
        """, (user_cgpa, user_branch, user_batch))
        rows = drives_cursor.fetchall()
        drives = [dict(row) for row in rows]
        conn.close()
        return drives

    @staticmethod
    def get_applied_drive_ids(student_id):
        conn = get_db()
        applied_cursor = conn.execute("SELECT drive_id FROM placement_applications WHERE student_id = %s", (student_id,))
        rows = applied_cursor.fetchall()
        ids = [row[0] for row in rows]
        conn.close()
        return ids

    @staticmethod
    def apply(drive_id, student_id, data):
        conn = get_db()
        conn.execute("""
            INSERT INTO placement_applications 
            (drive_id, student_id, contact_number, cover_letter, resume_url, linkedin_url)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (drive_id, student_id, data.get('contact'), data.get('cover_letter'), data.get('resume'), data.get('linkedin')))
        conn.commit()
        conn.close()

    @staticmethod
    def get_user_applications(student_id):
        conn = get_db()
        apps_cursor = conn.execute("""
            SELECT pd.company_name, pd.role, pa.applied_date, pa.status
            FROM placement_applications pa
            JOIN placement_drives pd ON pa.drive_id = pd.id
            WHERE pa.student_id = %s
            ORDER BY pa.applied_date DESC
        """, (student_id,))
        rows = apps_cursor.fetchall()
        apps = [dict(row) for row in rows]
        conn.close()
        return apps

    @staticmethod
    def get_drive_by_id(drive_id):
        conn = get_db()
        drive = conn.execute("SELECT * FROM placement_drives WHERE id = %s", (drive_id,)).fetchone()
        conn.close()
        return dict(drive) if drive else None
