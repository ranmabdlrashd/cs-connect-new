from database import db_connection


class InternalMark:
    @staticmethod
    def get_all_marks():
        with db_connection() as conn:
            marks = conn.execute("""
                SELECT i.sl_no, u.name as student_name, u.user_id as roll_no, 
                       i.subject_code, i.subject_name, i.internal_1, i.internal_2, 
                       i.assignment, i.total
                FROM internal_marks i
                JOIN users u ON i.user_id = u.user_id
                ORDER BY u.user_id ASC, i.subject_code ASC
            """).fetchall()
            return [dict(m) for m in marks]


    @staticmethod
    def update_marks(mark_id, in1, in2, assign):
        with db_connection() as conn:
            total = float(in1 or 0) + float(in2 or 0) + float(assign or 0)
            conn.execute("""
                UPDATE internal_marks 
                SET internal_1 = %s, internal_2 = %s, assignment = %s, total = %s
                WHERE sl_no = %s
            """, (in1, in2, assign, total, mark_id))
            conn.commit()
            return True

