def get_db():
    from app import get_db_connection

    return get_db_connection()


class Notification:
    @staticmethod
    def notify_admin(message, title='Admin Alert', category='Academic'):
        conn = get_db()
        # Find admins (role='admin')
        admins = conn.execute("SELECT id FROM users WHERE role = 'admin'").fetchall()
        for admin in admins:
            conn.execute(
                "INSERT INTO notifications (user_id, title, body, category) VALUES (%s, %s, %s, %s)",
                (admin[0], title, message, category),
            )
        conn.commit()
        conn.close()

    @staticmethod
    def notify_user(user_id, message, title='Notice', category='Academic'):
        conn = get_db()
        conn.execute(
            "INSERT INTO notifications (user_id, title, body, category) VALUES (%s, %s, %s, %s)",
            (user_id, title, message, category),
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
            SELECT id, title, body, category, created_at, is_read 
            FROM notifications 
            WHERE user_id = %s 
            ORDER BY created_at DESC
        """,
            (admin_id,),
        ).fetchall()

        # Mark as read
        conn.execute(
            "UPDATE notifications SET is_read = TRUE WHERE user_id = %s",
            (admin_id,),
        )
        conn.commit()
        conn.close()
        
        # for backwards compatibility with legacy templates
        result = []
        for n in notifs:
            d = dict(n)
            d['message'] = d['body']
            d['read_status'] = d['is_read']
            result.append(d)
        return result

    @staticmethod
    def get_user_notifications():
        from flask import session
        user_id = session.get("user_id")
        if not user_id:
            return []
        conn = get_db()
        # API requires: id, title, body, category, is_read, created_at
        notifs = conn.execute(
            """
            SELECT id, title, body, category, is_read, created_at 
            FROM notifications 
            WHERE user_id = %s 
            ORDER BY created_at DESC
        """,
            (user_id,),
        ).fetchall()
        conn.close()
        
        result = []
        for n in notifs:
            d = dict(n)
            # Create isoformat string for JS, and inject legacy fields for old templates
            d['created_at_iso'] = d['created_at'].isoformat() if d.get('created_at') else None
            d['message'] = d['body']
            d['read_status'] = d['is_read']
            result.append(d)
        return result

    @staticmethod
    def get_unread_count():
        from flask import session
        user_id = session.get("user_id")
        if not user_id:
            return 0
        conn = get_db()
        row = conn.execute(
            "SELECT COUNT(*) FROM notifications WHERE user_id = %s AND is_read = FALSE",
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
            "UPDATE notifications SET is_read = TRUE WHERE user_id = %s",
            (user_id,),
        )
        conn.commit()
        conn.close()

    @staticmethod
    def mark_read(notif_id):
        from flask import session
        user_id = session.get("user_id")
        if not user_id:
            return
        conn = get_db()
        conn.execute(
            "UPDATE notifications SET is_read = TRUE WHERE id = %s AND user_id = %s",
            (notif_id, user_id),
        )
        conn.commit()
        conn.close()
