def get_db():
    from app import get_db_connection

    return get_db_connection()


class Issue:
    @staticmethod
    def create_issue(book_id, user_id):
        conn = get_db()
        from datetime import datetime, timedelta
        issue_date = datetime.now()
        due_date = issue_date + timedelta(days=14)
        conn.execute(
            "INSERT INTO issues (book_id, user_id, status, due_date, issue_date) VALUES (%s, %s, 'issued', %s, %s)",
            (book_id, str(user_id), due_date, issue_date),
        )
        conn.commit()
        conn.close()

    @staticmethod
    def return_book(book_id):
        conn = get_db()
        conn.execute(
            "UPDATE issues SET status = 'returned', return_date = CURRENT_TIMESTAMP WHERE book_id = %s AND status = 'issued'",
            (book_id,),
        )
        conn.commit()
        conn.close()

    @staticmethod
    def has_user_issued_book(user_id, book_id):
        conn = get_db()
        issue = conn.execute(
            "SELECT sl_no FROM issues WHERE user_id = %s AND book_id = %s AND status = 'issued'",
            (str(user_id), book_id),
        ).fetchone()
        conn.close()
        return issue is not None

    @staticmethod
    def get_user_active_issued_count(user_id):
        conn = get_db()
        count = conn.execute(
            "SELECT COUNT(*) FROM issues WHERE user_id = %s AND status = 'issued'",
            (str(user_id),),
        ).fetchone()[0]
        conn.close()
        return count

    @staticmethod
    def has_outstanding_fines(user_id):
        conn = get_db()
        fine = conn.execute(
            "SELECT sl_no FROM issues_with_fines WHERE user_id = %s AND fine_amount > 0 AND payment_status != 'approved'",
            (str(user_id),),
        ).fetchone()
        conn.close()
        return fine is not None

    @staticmethod
    def is_user_issuer(user_id, book_id):
        return Issue.has_user_issued_book(user_id, book_id)

    @staticmethod
    def get_current_holder(book_id):
        conn = get_db()
        holder = conn.execute(
            """
            SELECT u.name 
            FROM issues i 
            JOIN users u ON i.user_id = u.user_id 
            WHERE i.book_id = %s AND i.status = 'issued'
        """,
            (book_id,),
        ).fetchone()
        conn.close()
        return holder[0] if holder else None

    @staticmethod
    def get_current_holder_id(book_id):
        conn = get_db()
        holder = conn.execute(
            "SELECT user_id FROM issues WHERE book_id = %s AND status = 'issued'",
            (book_id,),
        ).fetchone()
        conn.close()
        return holder[0] if holder else None

    @staticmethod
    def get_all_active_issues():
        conn = get_db()
        # Ensure we have these columns selected
        issues = conn.execute("""
            SELECT i.sl_no, i.issue_date, b.title as book_title, u.name as user_name
            FROM issues i
            JOIN books b ON i.book_id = b.sl_no
            JOIN users u ON i.user_id = u.user_id
            WHERE i.status = 'issued'
            ORDER BY i.issue_date DESC
        """).fetchall()
        conn.close()
        return [dict(i) for i in issues]

    @staticmethod
    def get_all_issues():
        conn = get_db()
        issues = conn.execute("""
            SELECT i.sl_no, i.issue_date, i.return_date, b.title as book_title, u.name as user_name, i.status, i.book_id
            FROM issues i
            JOIN books b ON i.book_id = b.sl_no
            JOIN users u ON i.user_id = u.user_id
            ORDER BY i.issue_date DESC
        """).fetchall()
        conn.close()
        return [dict(i) for i in issues]



    @staticmethod
    def get_history_by_book(book_id):
        conn = get_db()
        history = conn.execute("""
            SELECT i.sl_no, i.issue_date, i.return_date, i.status, u.name as user_name, u.user_id as admission_num
            FROM issues i
            JOIN users u ON i.user_id = u.user_id
            WHERE i.book_id = %s
            ORDER BY i.issue_date DESC
        """, (book_id,)).fetchall()
        conn.close()
        return [dict(h) for h in history]
