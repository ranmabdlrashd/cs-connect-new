def get_db():
    from app import get_db_connection

    return get_db_connection()


class Notification:
    @staticmethod
    def notify_admin(message):
        conn = get_db()
        # Find admins (role='admin')
        admins = conn.execute("SELECT id FROM users WHERE role = 'admin'").fetchall()
        for admin in admins:
            conn.execute(
                "INSERT INTO notifications (user_id, message) VALUES (%s, %s)",
                (admin[0], message),
            )
        conn.commit()
        conn.close()

    @staticmethod
    def notify_user(user_id, message):
        conn = get_db()
        conn.execute(
            "INSERT INTO notifications (user_id, message) VALUES (%s, %s)",
            (user_id, message),
        )
        conn.commit()
        conn.close()

    @staticmethod
    def get_admin_notifications():
        from flask import session

        admin_id = session.get("user_id")
        if not admin_id:
            return []

        conn = get_db()
        notifs = conn.execute(
            """
            SELECT id, message, created_at, read_status 
            FROM notifications 
            WHERE user_id = %s 
            ORDER BY created_at DESC
        """,
            (admin_id,),
        ).fetchall()

        # Mark as read
        conn.execute(
            "UPDATE notifications SET read_status = TRUE WHERE user_id = %s",
            (admin_id,),
        )
        conn.commit()
        conn.close()
        return [dict(n) for n in notifs]
    @staticmethod
    def get_user_notifications():
        from flask import session
        user_id = session.get("user_id")
        if not user_id:
            return []
        conn = get_db()
        notifs = conn.execute(
            """
            SELECT id, message, created_at, read_status 
            FROM notifications 
            WHERE user_id = %s 
            ORDER BY created_at DESC
            LIMIT 20
        """,
            (user_id,),
        ).fetchall()
        conn.close()
        return [dict(n) for n in notifs]

    @staticmethod
    def get_unread_count():
        from flask import session
        user_id = session.get("user_id")
        if not user_id:
            return 0
        conn = get_db()
        row = conn.execute(
            "SELECT COUNT(*) FROM notifications WHERE user_id = %s AND read_status = FALSE",
            (user_id,),
        ).fetchone()
        conn.close()
        return row[0] if row else 0

    @staticmethod
    def mark_all_read():
        from flask import session
        user_id = session.get("user_id")
        if not user_id:
            return
        conn = get_db()
        conn.execute(
            "UPDATE notifications SET read_status = TRUE WHERE user_id = %s",
            (user_id,),
        )
        conn.commit()
        conn.close()
