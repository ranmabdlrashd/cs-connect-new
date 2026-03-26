from database import get_db_connection



class Notification:
    @staticmethod
    def notify_admin(message, title='Admin Alert', category='Academic'):
        with get_db_connection() as conn:
            # Find admins (role='admin')
            admins = conn.execute("SELECT user_id FROM users WHERE role = 'admin'").fetchall()
            for admin in admins:
                conn.execute(
                    "INSERT INTO notifications (user_id, title, body, category) VALUES (%s, %s, %s, %s)",
                    (str(admin[0]), title, message, category),
                )
            conn.commit()


    @staticmethod
    def notify_user(user_id, message, title='Notice', category='Academic'):
        with get_db_connection() as conn:
            conn.execute(
                "INSERT INTO notifications (user_id, title, body, category) VALUES (%s, %s, %s, %s)",
                (str(user_id), title, message, category),
            )
            conn.commit()


    @staticmethod
    def get_admin_notifications():
        from flask import session

        admin_id = session.get("user_id")
        if not admin_id:
            return []

        with get_db_connection() as conn:
            notifs = conn.execute(
                """
                SELECT sl_no, title, body, category, created_at, is_read 
                FROM notifications 
                WHERE user_id = %s 
                ORDER BY created_at DESC
            """,
                (str(admin_id),),
            ).fetchall()
            # Mark as read
            conn.execute(
                "UPDATE notifications SET is_read = TRUE WHERE user_id = %s",
                (str(admin_id),),
            )
            conn.commit()

        
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
        with get_db_connection() as conn:
            # API requires: sl_no, title, body, category, is_read, created_at
            notifs = conn.execute(
                """
                SELECT sl_no, title, body, category, is_read, created_at 
                FROM notifications 
                WHERE user_id = %s 
                ORDER BY created_at DESC
            """,
                (str(user_id),),
            ).fetchall()

        
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
        with get_db_connection() as conn:
            row = conn.execute(
                "SELECT COUNT(*) FROM notifications WHERE user_id = %s AND is_read = FALSE",
                (str(user_id),),
            ).fetchone()
            return row[0] if row else 0


    @staticmethod
    def mark_all_read():
        from flask import session
        user_id = session.get("user_id")
        if not user_id:
            return
        with get_db_connection() as conn:
            conn.execute(
                "UPDATE notifications SET is_read = TRUE WHERE user_id = %s",
                (str(user_id),),
            )
            conn.commit()


    @staticmethod
    def mark_read(notif_id):
        from flask import session
        user_id = session.get("user_id")
        if not user_id:
            return
        with get_db_connection() as conn:
            conn.execute(
                "UPDATE notifications SET is_read = TRUE WHERE sl_no = %s AND user_id = %s",
                (notif_id, str(user_id)),
            )
            conn.commit()

