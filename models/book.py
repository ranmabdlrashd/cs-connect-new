from database import get_db_connection



class Book:
    @staticmethod
    def get_all():
        with get_db_connection() as conn:
            books = conn.execute("SELECT * FROM books").fetchall()
            return [dict(b) for b in books]


    @staticmethod
    def search(query):
        with get_db_connection() as conn:
            q = f"%{query}%"
            # Search by title, author, subject, keyword (description)
            # Using ILIKE for case insensitive search in Postgres
            sql = """
            SELECT * FROM books 
            WHERE title ILIKE %s OR author ILIKE %s 
            OR subject ILIKE %s OR description ILIKE %s
            """
            books = conn.execute(sql, (q, q, q, q)).fetchall()
            return [dict(b) for b in books]


    @staticmethod
    def get_by_id(book_id):
        with get_db_connection() as conn:
            book = conn.execute("SELECT * FROM books WHERE sl_no = %s", (book_id,)).fetchone()
            return dict(book) if book else None


    @staticmethod
    def update_availability(book_id, availability):
        with get_db_connection() as conn:
            conn.execute(
                "UPDATE books SET availability = %s WHERE sl_no = %s", (availability, book_id)
            )
            conn.commit()

