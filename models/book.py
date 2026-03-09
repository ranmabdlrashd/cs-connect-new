def get_db():
    from app import get_db_connection

    return get_db_connection()


class Book:
    @staticmethod
    def get_all():
        conn = get_db()
        books = conn.execute("SELECT * FROM books").fetchall()
        conn.close()
        return [dict(b) for b in books]

    @staticmethod
    def search(query):
        conn = get_db()
        q = f"%{query}%"
        # Search by title, author, subject, keyword (description)
        # Using ILIKE for case insensitive search in Postgres
        sql = """
        SELECT * FROM books 
        WHERE title ILIKE %s OR author ILIKE %s 
        OR subject ILIKE %s OR description ILIKE %s
        """
        books = conn.execute(sql, (q, q, q, q)).fetchall()
        conn.close()
        return [dict(b) for b in books]

    @staticmethod
    def get_by_id(book_id):
        conn = get_db()
        book = conn.execute("SELECT * FROM books WHERE id = %s", (book_id,)).fetchone()
        conn.close()
        return dict(book) if book else None

    @staticmethod
    def update_availability(book_id, availability):
        conn = get_db()
        conn.execute(
            "UPDATE books SET availability = %s WHERE id = %s", (availability, book_id)
        )
        conn.commit()
        conn.close()
