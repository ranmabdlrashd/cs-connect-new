from database import db_connection


class Placement:
    @staticmethod
    def get_user_profile(user_id):
        with db_connection() as conn:
            user = conn.execute("SELECT u.branch, u.batch, r.cgpa FROM users u LEFT JOIN results r ON u.user_id = r.student_id WHERE u.user_id = %s", (user_id,)).fetchone()
            return dict(user) if user else None



    @staticmethod
    def get_active_drives(user_cgpa, user_branch, user_batch):
        with db_connection() as conn:
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
            return drives


    @staticmethod
    def get_applied_drive_ids(student_id):
        with db_connection() as conn:
            applied_cursor = conn.execute("SELECT drive_id FROM placement_applications WHERE student_id = %s", (student_id,))
            rows = applied_cursor.fetchall()
            ids = [row[0] for row in rows]
            return ids


    @staticmethod
    def apply(drive_id, student_id, data):
        with db_connection() as conn:
            conn.execute("""
                INSERT INTO placement_applications 
                (drive_id, student_id, contact_number, cover_letter, resume_url, linkedin_url)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (drive_id, student_id, data.get('contact'), data.get('cover_letter'), data.get('resume'), data.get('linkedin')))
            conn.commit()


    @staticmethod
    def get_user_applications(student_id):
        with db_connection() as conn:
            apps_cursor = conn.execute("""
                SELECT pd.company_name, pd.role, pa.applied_date, pa.status
                FROM placement_applications pa
                JOIN placement_drives pd ON pa.drive_id = pd.sl_no
                WHERE pa.student_id = %s
                ORDER BY pa.applied_date DESC
            """, (student_id,))
            rows = apps_cursor.fetchall()
            apps = [dict(row) for row in rows]
            return apps


    @staticmethod
    def get_drive_by_id(drive_id):
        with db_connection() as conn:
            drive = conn.execute("SELECT * FROM placement_drives WHERE sl_no = %s", (drive_id,)).fetchone()
            return dict(drive) if drive else None

