from database import get_db_connection



class Issue:
    @staticmethod
    def create_issue(book_id, user_id):
        with get_db_connection() as conn:
            from datetime import datetime, timedelta
            issue_date = datetime.now()
            due_date = issue_date + timedelta(days=14)
            conn.execute(
                "INSERT INTO issues (book_id, user_id, status, due_date, issue_date) VALUES (%s, %s, 'issued', %s, %s)",
                (book_id, str(user_id), due_date, issue_date),
            )
            conn.commit()


    @staticmethod
    def return_book(book_id):
        with get_db_connection() as conn:
            conn.execute(
                "UPDATE issues SET status = 'returned', return_date = CURRENT_TIMESTAMP WHERE book_id = %s AND status = 'issued'",
                (book_id,),
            )
            conn.commit()


    @staticmethod
    def has_user_issued_book(user_id, book_id):
        with get_db_connection() as conn:
            issue = conn.execute(
                "SELECT sl_no FROM issues WHERE user_id = %s AND book_id = %s AND status = 'issued'",
                (str(user_id), book_id),
            ).fetchone()
            return issue is not None


    @staticmethod
    def get_user_active_issued_count(user_id):
        with get_db_connection() as conn:
            count = conn.execute(
                "SELECT COUNT(*) FROM issues WHERE user_id = %s AND status = 'issued'",
                (str(user_id),),
            ).fetchone()[0]
            return count


    @staticmethod
    def has_outstanding_fines(user_id):
        with get_db_connection() as conn:
            fine = conn.execute(
                "SELECT sl_no FROM issues_with_fines WHERE user_id = %s AND fine_amount > 0 AND payment_status != 'approved'",
                (str(user_id),),
            ).fetchone()
            return fine is not None


    @staticmethod
    def is_user_issuer(user_id, book_id):
        return Issue.has_user_issued_book(user_id, book_id)

    @staticmethod
    def get_current_holder(book_id):
        with get_db_connection() as conn:
            holder = conn.execute(
                """
                SELECT u.name 
                FROM issues i 
                JOIN users u ON i.user_id = u.user_id 
                WHERE i.book_id = %s AND i.status = 'issued'
            """,
                (book_id,),
            ).fetchone()
            return holder[0] if holder else None


    @staticmethod
    def get_current_holder_id(book_id):
        with get_db_connection() as conn:
            holder = conn.execute(
                "SELECT user_id FROM issues WHERE book_id = %s AND status = 'issued'",
                (book_id,),
            ).fetchone()
            return holder[0] if holder else None


    @staticmethod
    def get_all_active_issues():
        with get_db_connection() as conn:
            # Ensure we have these columns selected
            issues = conn.execute("""
                SELECT i.sl_no, i.issue_date, b.title as book_title, u.name as user_name
                FROM issues i
                JOIN books b ON i.book_id = b.sl_no
                JOIN users u ON i.user_id = u.user_id
                WHERE i.status = 'issued'
                ORDER BY i.issue_date DESC
            """).fetchall()
            return [dict(i) for i in issues]


    @staticmethod
    def get_all_issues():
        with get_db_connection() as conn:
            issues = conn.execute("""
                SELECT i.sl_no, i.issue_date, i.return_date, b.title as book_title, u.name as user_name, i.status, i.book_id
                FROM issues i
                JOIN books b ON i.book_id = b.sl_no
                JOIN users u ON i.user_id = u.user_id
                ORDER BY i.issue_date DESC
            """).fetchall()
            return [dict(i) for i in issues]




    @staticmethod
    def get_history_by_book(book_id):
        with get_db_connection() as conn:
            history = conn.execute("""
                SELECT i.sl_no, i.issue_date, i.return_date, i.status, u.name as user_name, u.user_id as admission_num
                FROM issues i
                JOIN users u ON i.user_id = u.user_id
                WHERE i.book_id = %s
                ORDER BY i.issue_date DESC
            """, (book_id,)).fetchall()
            return [dict(h) for h in history]

