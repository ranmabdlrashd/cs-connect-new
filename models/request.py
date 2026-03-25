def get_db():
    from app import get_db_connection

    return get_db_connection()


class Request:
    @staticmethod
    def create_request(book_id, user_id, request_type='reserve'):
        conn = get_db()
        req = conn.execute(
            "INSERT INTO requests (book_id, requested_by, request_type, status) VALUES (%s, %s, %s, 'pending') RETURNING id",
            (book_id, user_id, request_type),
        ).fetchone()
        conn.commit()
        conn.close()
        return req['id'] if req else None

    @staticmethod
    def get_by_id(request_id):
        conn = get_db()
        req = conn.execute(
            "SELECT * FROM requests WHERE id = %s", (request_id,)
        ).fetchone()
        conn.close()
        return dict(req) if req else None

    @staticmethod
    def mark_processed(request_id, feedback=None):
        conn = get_db()
        conn.execute(
            "UPDATE requests SET status = 'processed', admin_feedback = %s WHERE id = %s", (feedback, request_id)
        )
        conn.commit()
        conn.close()

    @staticmethod
    def reject(request_id, feedback=None):
        conn = get_db()
        conn.execute(
            "UPDATE requests SET status = 'rejected', admin_feedback = %s WHERE id = %s", (feedback, request_id)
        )
        conn.commit()
        conn.close()

    @staticmethod
    def get_all_pending_requests():
        conn = get_db()
        reqs = conn.execute("""
            SELECT r.id, r.request_date, b.title as book_title, u.name as user_name, r.book_id, r.request_type, r.requested_by
            FROM requests r
            JOIN books b ON r.book_id = b.id
            JOIN users u ON r.requested_by = u.id
            WHERE r.status = 'pending'
            ORDER BY r.request_date ASC
        """).fetchall()
        conn.close()
        return [dict(r) for r in reqs]

    @staticmethod
    def get_pending_requests_by_book(book_id):
        conn = get_db()
        reqs = conn.execute("""
            SELECT r.id, r.request_date, b.title as book_title, u.name as user_name, r.book_id
            FROM requests r
            JOIN books b ON r.book_id = b.id
            JOIN users u ON r.requested_by = u.id
            WHERE r.status = 'pending' AND r.book_id = %s
            ORDER BY r.request_date ASC
        """, (book_id,)).fetchall()
        conn.close()
        return [dict(r) for r in reqs]


    @staticmethod
    def get_all_requests():
        conn = get_db()
        reqs = conn.execute("""
            SELECT r.id, r.request_date, b.title as book_title, u.name as user_name, r.status, r.book_id, r.request_type
            FROM requests r
            JOIN books b ON r.book_id = b.id
            JOIN users u ON r.requested_by = u.id
            ORDER BY r.request_date DESC
        """).fetchall()
        conn.close()
        return [dict(r) for r in reqs]

    @staticmethod
    def has_pending_request(user_id, book_id, request_type):
        conn = get_db()
        req = conn.execute(
            "SELECT id FROM requests WHERE requested_by = %s AND book_id = %s AND request_type = %s AND status = 'pending'",
            (user_id, book_id, request_type),
        ).fetchone()
        conn.close()
        return req is not None
