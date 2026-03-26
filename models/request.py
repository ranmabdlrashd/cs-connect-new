from database import get_db_connection



class Request:
    @staticmethod
    def create_request(book_id, user_id, request_type='reserve'):
        with get_db_connection() as conn:
            req = conn.execute(
                "INSERT INTO requests (book_id, requested_by, request_type, status) VALUES (%s, %s, %s, 'pending') RETURNING sl_no",
                (book_id, str(user_id), request_type),
            ).fetchone()
            conn.commit()
            return req['sl_no'] if req else None


    @staticmethod
    def get_by_id(request_id):
        with get_db_connection() as conn:
            req = conn.execute(
                "SELECT * FROM requests WHERE sl_no = %s", (request_id,)
            ).fetchone()
            return dict(req) if req else None


    @staticmethod
    def mark_processed(request_id, feedback=None):
        with get_db_connection() as conn:
            conn.execute(
                "UPDATE requests SET status = 'processed', admin_feedback = %s WHERE sl_no = %s", (feedback, request_id)
            )
            conn.commit()


    @staticmethod
    def reject(request_id, feedback=None):
        with get_db_connection() as conn:
            conn.execute(
                "UPDATE requests SET status = 'rejected', admin_feedback = %s WHERE sl_no = %s", (feedback, request_id)
            )
            conn.commit()


    @staticmethod
    def get_all_pending_requests():
        with get_db_connection() as conn:
            reqs = conn.execute("""
                SELECT r.sl_no, r.request_date, b.title as book_title, u.name as user_name, r.book_id, r.request_type, r.requested_by
                FROM requests r
                JOIN books b ON r.book_id = b.sl_no
                JOIN users u ON r.requested_by = u.user_id
                WHERE r.status = 'pending'
                ORDER BY r.request_date ASC
            """).fetchall()
            return [dict(r) for r in reqs]


    @staticmethod
    def get_pending_requests_by_book(book_id):
        with get_db_connection() as conn:
            reqs = conn.execute("""
                SELECT r.sl_no, r.request_date, b.title as book_title, u.name as user_name, r.book_id
                FROM requests r
                JOIN books b ON r.book_id = b.sl_no
                JOIN users u ON r.requested_by = u.user_id
                WHERE r.status = 'pending' AND r.book_id = %s
                ORDER BY r.request_date ASC
            """, (book_id,)).fetchall()
            return [dict(r) for r in reqs]



    @staticmethod
    def get_all_requests():
        with get_db_connection() as conn:
            reqs = conn.execute("""
                SELECT r.sl_no, r.request_date, b.title as book_title, u.name as user_name, r.status, r.book_id, r.request_type
                FROM requests r
                JOIN books b ON r.book_id = b.sl_no
                JOIN users u ON r.requested_by = u.user_id
                ORDER BY r.request_date DESC
            """).fetchall()
            return [dict(r) for r in reqs]


    @staticmethod
    def has_pending_request(user_id, book_id, request_type):
        with get_db_connection() as conn:
            req = conn.execute(
                "SELECT sl_no FROM requests WHERE requested_by = %s AND book_id = %s AND request_type = %s AND status = 'pending'",
                (str(user_id), book_id, request_type),
            ).fetchone()
            return req is not None

