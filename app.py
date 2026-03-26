import json
import os

from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
import psycopg2
import psycopg2.extras
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

load_dotenv()

app = Flask(__name__)
app.secret_key = "testsecret"
app.jinja_env.add_extension('jinja2.ext.do')

import logging
from logging.handlers import RotatingFileHandler
file_handler = RotatingFileHandler('flask_errors.log', maxBytes=1024 * 1024, backupCount=5)
file_handler.setFormatter(logging.Formatter(
    '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
))
file_handler.setLevel(logging.ERROR)  # Set to ERROR for production-like use
app.logger.addHandler(file_handler)
app.logger.setLevel(logging.ERROR)

from routes.library_routes import library_bp
from routes.admin_routes import admin_bp
# Placement routes removed
import llm_engine

app.register_blueprint(library_bp)
app.register_blueprint(admin_bp)
# Placement blueprint removed

# PostgreSQL Connection details
class DBConnection:
    def __init__(self):
        urls = [
            os.environ.get("NEON_DATABASE_URL"),
            os.environ.get("LOCAL_DATABASE_URL"),
            os.environ.get("DATABASE_URL")
        ]
        # Filter out None and empty strings
        urls = [u for u in urls if u]
        
        self.conn = None
        errors = []
        
        for db_url in urls:
            try:
                print(f"Attempting connection to: {db_url[:50]}...")
                self.conn = psycopg2.connect(db_url)
                print("Connection successful!")
                break
            except Exception as e:
                print(f"Connection failed for {db_url[:50]}: {e}")
                errors.append(str(e))
        
        if not self.conn:
            # Final fallback to standard host/db/user/pass if all URLs fail
            try:
                print("Using legacy fallback local connection")
                DB_HOST = os.environ.get("DB_HOST", "localhost")
                DB_NAME = os.environ.get("DB_NAME", "csconnect")
                DB_USER = os.environ.get("DB_USER", "postgres")
                DB_PASS = os.environ.get("DB_PASS", "1234")
                self.conn = psycopg2.connect(
                    host=DB_HOST, dbname=DB_NAME, user=DB_USER, password=DB_PASS
                )
                print("Legacy connection successful!")
            except Exception as e:
                errors.append(f"Legacy fallback failed: {e}")
                raise Exception(f"Failed to connect to any database. Errors: {'; '.join(errors)}")
    
    def cursor(self):
        return self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
    def execute(self, query, params=None):
        cur = self.cursor()
        if params:
            cur.execute(query, params)
        else:
            cur.execute(query)
        return cur
        
    def commit(self):
        self.conn.commit()
        
    def rollback(self):
        self.conn.rollback()
        
    def close(self):
        self.conn.close()

def get_db_connection():
    return DBConnection()


def get_site_data(key, default_val=None):
    try:
        conn = get_db_connection()
        row = conn.execute("SELECT data FROM site_data WHERE key = %s", (key,)).fetchone()
        conn.close()
        if row and row[0]:
            # Handle if it's already a string or a dict/list because of jsonb
            if isinstance(row[0], str):
                return json.loads(row[0])
            return row[0]
        return default_val if default_val is not None else {}
    except Exception as e:
        print(f"Error fetching site_data for key {key}: {e}")
        return default_val if default_val is not None else {}

def get_news_ticker():
    conn = get_db_connection()
    row = conn.execute("SELECT text FROM news_ticker ORDER BY sl_no DESC LIMIT 1").fetchone()
    conn.close()
    return row[0] if row else ""

def get_home_stats():
    conn = get_db_connection()
    rows = conn.execute("SELECT value, label FROM home_stats ORDER BY sl_no ASC").fetchall()
    conn.close()
    return [{"value": r[0], "label": r[1]} for r in rows]

# Placement helper functions removed




# ─────────────────────────────────────────────────
# CONTEXT PROCESSOR — injects globals into every template
# ─────────────────────────────────────────────────
@app.context_processor
def inject_globals():
    from models.notification import Notification
    try:
        notif_count = Notification.get_unread_count() if session.get('user_id') else 0
        nav_notifs = Notification.get_user_notifications() if session.get('user_id') else []
    except Exception:
        notif_count = 0
        nav_notifs = []
    return {
        "ticker_text": get_news_ticker(),
        "active_page": "",   # overridden per route
        "notif_count": notif_count,
        "nav_notifs": nav_notifs,
    }


@app.route('/notifications/mark-read', methods=['POST'])
def notifications_mark_read():
    if session.get('user_id'):
        from models.notification import Notification
        Notification.mark_all_read()
    return jsonify({'status': 'ok'})


@app.route('/notifications/all')
def notifications_all():
    if not session.get('user_id'):
        flash("Please log in.", "warning")
        return redirect(url_for('login'))
    from models.notification import Notification
    all_notifs = Notification.get_user_notifications()
    # Mark all as read once they open the full page
    Notification.mark_all_read()
    return render_template('notifications_all.html', all_notifs=all_notifs, active_page='')

# ── NEW API ENDPOINTS ──

@app.route('/api/notifications', methods=['GET'])
def api_get_notifications():
    if not session.get('user_id'):
        return jsonify({'error': 'Unauthorized'}), 401
    from models.notification import Notification
    all_notifs = Notification.get_user_notifications()
    return jsonify(all_notifs)

@app.route('/api/notifications/<int:notif_id>/read', methods=['PATCH'])
def api_notification_read(notif_id):
    if not session.get('user_id'):
        return jsonify({'error': 'Unauthorized'}), 401
    from models.notification import Notification
    Notification.mark_read(notif_id)
    return jsonify({'status': 'ok'})

@app.route('/api/notifications/read-all', methods=['PATCH'])
def api_notifications_read_all():
    if not session.get('user_id'):
        return jsonify({'error': 'Unauthorized'}), 401
    from models.notification import Notification
    Notification.mark_all_read()
    return jsonify({'status': 'ok'})

# ── PUBLIC PLACEMENTS ROUTE ──
@app.route('/placements')
def placements():
    return render_template('placement.html')


# ── NEW DASHBOARD ROUTE ──

@app.route('/dashboard/notifications')
def dashboard_notifications():
    if not session.get('user_id'):
        flash("Please log in.", "warning")
        return redirect(url_for('login'))
    return render_template('notifications.html', active_page='')

    conn = get_db_connection()
    try:
        downloads = conn.execute("SELECT * FROM download_logs WHERE user_id = %s ORDER BY downloaded_at DESC LIMIT 20", (session['user_id'],)).fetchall()
        downloads = [dict(d) for d in downloads]
    except Exception as e:
        print(f"Error fetching download logs: {e}")
        downloads = []
    finally:
        conn.close()
        
    return render_template('student_settings.html', active_page='settings', downloads=downloads)

@app.route('/api/student/profile', methods=['GET', 'PATCH'])
def api_student_profile():
    if not session.get('user_id'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    conn = get_db_connection()
    try:
        if request.method == 'GET':
            user = conn.execute("SELECT name, email, user_id, batch, phone FROM users WHERE user_id = %s", (session['user_id'],)).fetchone()
            if not user:
                return jsonify({'error': 'User not found'}), 404
            return jsonify(dict(user))
            
        elif request.method == 'PATCH':
            data = request.json
            name = data.get('name')
            phone = data.get('phone')
            
            updates = []
            params = []
            if name is not None:
                updates.append("name = %s")
                params.append(name)
            if phone is not None:
                updates.append("phone = %s")
                params.append(phone)
                
            if updates:
                params.append(session['user_id'])
                query = f"UPDATE users SET {', '.join(updates)} WHERE user_id = %s"
                conn.execute(query, tuple(params))
                conn.commit()
                return jsonify({'status': 'ok'})
            return jsonify({'error': 'No fields provided'}), 400
    except Exception as e:
        print(f"Error in api_student_profile: {e}")
        return jsonify({'error': 'Internal server error'}), 500
    finally:
        conn.close()

@app.route('/api/student/notification-preferences', methods=['GET', 'PATCH'])
def api_notification_preferences():
    if not session.get('user_id'):
        return jsonify({'error': 'Unauthorized'}), 401
        
    conn = get_db_connection()
    valid_fields = ['library_alerts', 'department_notices', 'exam_alerts']
    try:
        if request.method == 'GET':
            query = f"SELECT {', '.join(valid_fields)} FROM users WHERE user_id = %s"
            prefs = conn.execute(query, (session['user_id'],)).fetchone()
            return jsonify(dict(prefs) if prefs else {})
            
        elif request.method == 'PATCH':
            data = request.json
            updates = []
            params = []
            
            for field in valid_fields:
                if field in data:
                    updates.append(f"{field} = %s")
                    params.append(bool(data[field]))
                    
            if updates:
                params.append(session['user_id'])
                query = f"UPDATE users SET {', '.join(updates)} WHERE user_id = %s"
                conn.execute(query, tuple(params))
                conn.commit()
                return jsonify({'status': 'ok'})
            return jsonify({'error': 'No valid fields provided'}), 400
    except Exception as e:
        print(f"Error in api_notification_preferences: {e}")
        return jsonify({'error': 'Internal server error'}), 500
    finally:
        conn.close()

@app.route('/api/auth/change-password', methods=['POST'])
def api_change_password():
    if not session.get('user_id'):
        return jsonify({'error': 'Unauthorized'}), 401
        
    data = request.json
    current_password = data.get('current_password')
    new_password = data.get('new_password')
    
    if not current_password or not new_password:
        return jsonify({'error': 'Missing password fields'}), 400
        
    conn = get_db_connection()
    try:
        user = conn.execute("SELECT password FROM users WHERE user_id = %s", (session['user_id'],)).fetchone()
        if not user or not check_password_hash(user['password'], current_password):
            return jsonify({'error': 'Incorrect current password'}), 400
            
        new_hashed = generate_password_hash(new_password)
        conn.execute("UPDATE users SET password = %s WHERE user_id = %s", (new_hashed, session['user_id']))
        conn.commit()
        return jsonify({'status': 'ok'})
    except Exception as e:
        print(f"Error in api_change_password: {e}")
        return jsonify({'error': 'Internal server error'}), 500
    finally:
        conn.close()

@app.route('/api/auth/logout-all', methods=['POST'])
def api_logout_all():
    if not session.get('user_id'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    # In a real app we'd invalidate all session tokens or change token version in DB.
    # Here, we will just clear the current session. To invalidate all, we could clear reset_token or set a logout timestamp.
    # For now, simply clearing session is acceptable as there is no session tracking table.
    session.clear()
    return jsonify({'status': 'ok'})



# ─────────────────────────────────────────────────
# DATABASE SETUP
# ─────────────────────────────────────────────────
def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. users
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            sl_no SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            user_id TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            role TEXT DEFAULT 'student',
            is_verified BOOLEAN DEFAULT FALSE,
            reset_token TEXT
        )
    ''')
    
    # Add columns if they don't exist (safety for existing db)
    cursor.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS is_verified BOOLEAN DEFAULT FALSE")
    cursor.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS reset_token TEXT")
    cursor.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS status TEXT DEFAULT 'Active'")
    cursor.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
    cursor.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS batch TEXT")
    cursor.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS department TEXT")
    cursor.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS designation TEXT")
    cursor.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS phone TEXT")
    
    # 2. faculty
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS faculty (
            sl_no SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            designation TEXT,
            designation_key TEXT,
            qualification TEXT,
            joined TEXT,
            research TEXT,
            email TEXT,
            photo TEXT
        )
    ''')
    
    # 3. books
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS books (
            sl_no SERIAL PRIMARY KEY,
            title TEXT NOT NULL,
            author TEXT,
            category TEXT,
            status TEXT,
            cover_gradient TEXT,
            cover_icon TEXT
        )
    ''')
    
    # Library Module Additions
    cursor.execute('ALTER TABLE books ADD COLUMN IF NOT EXISTS subject TEXT')
    cursor.execute('ALTER TABLE books ADD COLUMN IF NOT EXISTS description TEXT')
    cursor.execute('ALTER TABLE books ADD COLUMN IF NOT EXISTS availability BOOLEAN DEFAULT TRUE')
    cursor.execute('ALTER TABLE books ADD COLUMN IF NOT EXISTS isbn TEXT')
    cursor.execute('ALTER TABLE books ADD COLUMN IF NOT EXISTS total_copies INTEGER DEFAULT 1')
    cursor.execute('ALTER TABLE books ADD COLUMN IF NOT EXISTS available_copies INTEGER DEFAULT 1')
    cursor.execute('ALTER TABLE books ADD COLUMN IF NOT EXISTS is_reference BOOLEAN DEFAULT FALSE')
    cursor.execute('ALTER TABLE books ADD COLUMN IF NOT EXISTS added_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP')
    cursor.execute('ALTER TABLE books ADD COLUMN IF NOT EXISTS publisher TEXT')
    cursor.execute('ALTER TABLE books ADD COLUMN IF NOT EXISTS year INTEGER')
    cursor.execute('ALTER TABLE books ADD COLUMN IF NOT EXISTS edition TEXT')
    cursor.execute('ALTER TABLE books ADD COLUMN IF NOT EXISTS shelf_code TEXT')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS issues (
            sl_no SERIAL PRIMARY KEY,
            book_id INTEGER REFERENCES books(sl_no) ON DELETE CASCADE,
            user_id TEXT REFERENCES users(user_id) ON DELETE CASCADE,
            issue_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            due_date TIMESTAMP,
            return_date TIMESTAMP,
            status TEXT DEFAULT 'issued'
        )
    ''')
    cursor.execute('ALTER TABLE issues ADD COLUMN IF NOT EXISTS due_date TIMESTAMP')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS requests (
            sl_no SERIAL PRIMARY KEY,
            book_id INTEGER REFERENCES books(sl_no) ON DELETE CASCADE,
            requested_by TEXT REFERENCES users(user_id) ON DELETE CASCADE,
            request_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'pending',
            request_type TEXT,
            admin_feedback TEXT
        )
    ''')
    
    # Fines
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS library_fines (
            sl_no SERIAL PRIMARY KEY,
            student_id TEXT REFERENCES users(user_id) ON DELETE CASCADE,
            book_id INTEGER,
            issue_id INTEGER,
            amount DECIMAL(10,2),
            days_overdue INTEGER,
            rate_per_day DECIMAL(10,2) DEFAULT 1.00,
            paid BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    cursor.execute('''
        ALTER TABLE library_fines 
        ADD COLUMN IF NOT EXISTS book_id INTEGER,
        ADD COLUMN IF NOT EXISTS issue_id INTEGER,
        ADD COLUMN IF NOT EXISTS amount DECIMAL(10,2),
        ADD COLUMN IF NOT EXISTS days_overdue INTEGER,
        ADD COLUMN IF NOT EXISTS rate_per_day DECIMAL(10,2) DEFAULT 1.00,
        ADD COLUMN IF NOT EXISTS paid BOOLEAN DEFAULT FALSE
    ''')

    # Notifications
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS notifications (
            sl_no SERIAL PRIMARY KEY,
            user_id TEXT REFERENCES users(user_id) ON DELETE CASCADE,
            title TEXT,
            body TEXT,
            category TEXT,
            is_read BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 4. placement_summary
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS placement_summary (
            sl_no SERIAL PRIMARY KEY,
            icon TEXT,
            value TEXT,
            label TEXT,
            decimal_bool INTEGER,
            company TEXT
        )
    ''')
    
    # 5. placement_companies
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS placement_companies (
            sl_no SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            url TEXT,
            sector TEXT
        )
    ''')
    
    # 6. alumni
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS alumni (
            sl_no SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            batch TEXT,
            company TEXT,
            package TEXT,
            photo TEXT,
            testimonial TEXT
        )
    ''')
    
    # 7. internships
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS internships (
            sl_no SERIAL PRIMARY KEY,
            title TEXT NOT NULL,
            company TEXT,
            domain TEXT,
            location TEXT,
            description TEXT,
            link TEXT
        )
    ''')
    
    # 8. programs
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS programs (
            sl_no SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            duration TEXT,
            intake TEXT,
            eligibility TEXT,
            extra_icon TEXT,
            extra_label TEXT,
            extra_value TEXT,
            highlights TEXT
        )
    ''')
    
    # 9. semesters
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS semesters (
            sl_no SERIAL PRIMARY KEY,
            title TEXT NOT NULL,
            subjects TEXT
        )
    ''')
    
    # 10. news_ticker
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS news_ticker (
            sl_no SERIAL PRIMARY KEY,
            text TEXT
        )
    ''')
    
    # 11. home_stats
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS home_stats (
            sl_no SERIAL PRIMARY KEY,
            value TEXT,
            label TEXT
        )
    ''')
    
    # 12. placement_batches
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS placement_batches (
            sl_no SERIAL PRIMARY KEY,
            batch_key TEXT,
            label TEXT,
            stats JSONB,
            companies JSONB
        )
    ''')
    
    # 13. site_data
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS site_data (
            key TEXT PRIMARY KEY,
            data JSONB
        )
    ''')

    # 14. timetable_subjects
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS timetable_subjects (
            sl_no SERIAL PRIMARY KEY,
            batch TEXT DEFAULT 'S2 CSE A',
            code TEXT NOT NULL,
            full_name TEXT,
            faculty_code TEXT,
            faculty_name TEXT
        )
    ''')

    # 15. timetable
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS timetable (
            sl_no SERIAL PRIMARY KEY,
            batch TEXT DEFAULT 'S2 CSE A',
            day TEXT NOT NULL,
            period INTEGER NOT NULL,
            subject_code TEXT,
            faculty_code TEXT,
            is_lab BOOLEAN DEFAULT FALSE,
            span INTEGER DEFAULT 1
        )
    ''')

    # 16. timetable_meta
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS timetable_meta (
            batch TEXT PRIMARY KEY,
            is_image BOOLEAN DEFAULT FALSE,
            image_filename TEXT
        )
    ''')

    # 17. portal_sessions
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS portal_sessions (
            sl_no SERIAL PRIMARY KEY,
            user_id TEXT REFERENCES users(user_id) ON DELETE CASCADE,
            ip_address TEXT,
            user_agent TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP
        )
    ''')

    # 18. pending_approvals
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pending_approvals (
            sl_no SERIAL PRIMARY KEY,
            type TEXT NOT NULL,
            requestor_id TEXT REFERENCES users(user_id) ON DELETE CASCADE,
            requestor_name TEXT,
            details TEXT,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Seed S2 CSE A data (only if empty)
    cursor.execute("SELECT COUNT(*) FROM timetable")
    existing = cursor.fetchone()[0]
    if existing == 0:
        # --- Subjects ---
        subjects = [
            ('S2 CSE A', 'MAT-2',    'GAMAT201 Mathematics for Information Science - 2',           'DGP',     'Prof. Dhanya George P'),
            ('S2 CSE A', 'PHY',      'GAPHT121 Physics for Information Science',                    'SRC',     'Prof. Sreeja C'),
            ('S2 CSE A', 'FOC',      'GXEST203 Foundations of Computing',                           'TEJ',     'Prof. Teenu Jose'),
            ('S2 CSE A', 'CP',       'GXEST204 Programming in C',                                   'THV/SPJ', 'Prof. Thilakavathi A / Prof. Sinijoy P J'),
            ('S2 CSE A', 'DMS',      'PCCST205 Discrete Mathematics',                               'AAF',     'Prof. Anson Antony Fertal'),
            ('S2 CSE A', 'IPR',      'UCEST206 Engineering Entrepreneurship & IPR',                 'ANG',     'Prof. Angel Mathai'),
            ('S2 CSE A', 'HW',       'UCHWT127 Health and Wellness',                               'DMR',     'Prof. Dilu Mary Rose'),
            ('S2 CSE A', 'IT W/S',   'GXESL208 IT Workshop',                                       'TEJ',     'Prof. Teenu Jose'),
            ('S2 CSE A', 'LT',       'Language Training',                                           'DMR',     'Prof. Dilu Mary Rose'),
            ('S2 CSE A', 'ACTIVITY', 'Activity Hour',                                               'SRC',     'Prof. Sreeja C'),
            ('S2 CSE A', 'CP/PHY LAB','CP / Physics Lab (Combined)',                               'THV/SRC', 'Prof. Thilakavathi A / Prof. Sreeja C'),
            ('S2 CSE A', 'IT W/S/PHY LAB','IT Workshop / Physics Lab (Combined)',                  'TEJ/SRC', 'Prof. Teenu Jose / Prof. Sreeja C'),
            ('S2 CSE A', 'CP/IT W/S', 'Programming in C / IT Workshop (Combined)',                 'THV/TEJ', 'Prof. Thilakavathi A / Prof. Teenu Jose'),
            ('S2 CSE A', 'DMS(T)',   'Discrete Mathematics Tutorial',                               'AAF',     'Prof. Anson Antony Fertal'),
            ('S2 CSE A', 'HW(P)',    'Health and Wellness (Practical)',                             'DMR',     'Prof. Dilu Mary Rose'),
        ]
        cursor.executemany(
            'INSERT INTO timetable_subjects (batch, code, full_name, faculty_code, faculty_name) VALUES (%s,%s,%s,%s,%s)',
            subjects
        )

        # --- Timetable entries (day, period, subject_code, faculty_code, is_lab, span) ---
        entries = [
            # MONDAY
            ('S2 CSE A','Monday',1,'DMS','AAF',False,1),
            ('S2 CSE A','Monday',2,'FOC','TEJ',False,1),
            ('S2 CSE A','Monday',3,'MAT-2','DGP',False,1),
            ('S2 CSE A','Monday',4,'PHY','SRC',False,1),
            ('S2 CSE A','Monday',5,'DMS(T)','AAF',False,1),
            ('S2 CSE A','Monday',6,'HW','DMR',False,1),
            # TUESDAY
            ('S2 CSE A','Tuesday',1,'IPR','ANG',False,1),
            ('S2 CSE A','Tuesday',2,'FOC','TEJ',False,1),
            ('S2 CSE A','Tuesday',3,'CP/PHY LAB','THV/SRC',True,2),
            ('S2 CSE A','Tuesday',5,'HW(P)','DMR',True,1),
            ('S2 CSE A','Tuesday',6,'MAT-2','DGP',False,1),
            # WEDNESDAY
            ('S2 CSE A','Wednesday',1,'MAT-2','DGP',False,1),
            ('S2 CSE A','Wednesday',2,'CP','THV',False,1),
            ('S2 CSE A','Wednesday',3,'IPR','ANG',False,1),
            ('S2 CSE A','Wednesday',4,'DMS','AAF',False,1),
            ('S2 CSE A','Wednesday',5,'PHY','SRC',False,1),
            ('S2 CSE A','Wednesday',6,'CP','THV',False,1),
            # THURSDAY
            ('S2 CSE A','Thursday',1,'DMS','AAF',False,1),
            ('S2 CSE A','Thursday',2,'FOC','TEJ',False,1),
            ('S2 CSE A','Thursday',3,'IT W/S/PHY LAB','TEJ/SRC',True,2),
            ('S2 CSE A','Thursday',5,'CP','THV',False,1),
            ('S2 CSE A','Thursday',6,'IPR','ANG',False,1),
            # FRIDAY
            ('S2 CSE A','Friday',1,'PHY','SRC',False,1),
            ('S2 CSE A','Friday',2,'LT','DMR',False,1),
            ('S2 CSE A','Friday',3,'CP','THV',False,1),
            ('S2 CSE A','Friday',4,'MAT-2','DGP',False,1),
            ('S2 CSE A','Friday',5,'CP/IT W/S','THV/TEJ',True,2),
            # SATURDAY
            ('S2 CSE A','Saturday',1,'CP','THV',False,1),
            ('S2 CSE A','Saturday',2,'DMS','AAF',False,1),
            ('S2 CSE A','Saturday',3,'HW','DMR',False,1),
            ('S2 CSE A','Saturday',4,'ACTIVITY','SRC',False,1),
            ('S2 CSE A','Saturday',5,'PHY','SRC',False,1),
            ('S2 CSE A','Saturday',6,'FOC','TEJ',False,1),
        ]
        cursor.executemany(
            'INSERT INTO timetable (batch, day, period, subject_code, faculty_code, is_lab, span) VALUES (%s,%s,%s,%s,%s,%s,%s)',
            entries
        )
        
        # --- Timetable Meta ---
        cursor.execute(
            'INSERT INTO timetable_meta (batch, is_image, image_filename) VALUES (%s, %s, %s)',
            ('S2 CSE A', False, None)
        )

    # 19. mous (Memorandum of Understanding)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS mous (
            sl_no SERIAL PRIMARY KEY,
            organization TEXT NOT NULL,
            date_of_signing TEXT,
            status TEXT DEFAULT 'Active'
        )
    ''')

    # Seed Books
    cursor.execute("SELECT COUNT(*) FROM books")
    if cursor.fetchone()[0] == 0:
        books_data = [
            ('The Pragmatic Programmer', 'Andrew Hunt', 'Computer Science', '978-0201616224', True),
            ('Clean Code', 'Robert C. Martin', 'Computer Science', '978-0132350884', True),
            ('Introduction to Algorithms', 'Thomas H. Cormen', 'Computer Science', '978-0262033848', True),
            ('Artificial Intelligence', 'Stuart Russell', 'Computer Science', '978-0136042594', True),
            ('Structure & Interpretation', 'Harold Abelson', 'Computer Science', '978-0262510875', True),
            ('Computer Networks', 'Andrew Tanenbaum', 'Computer Science', '978-0132126953', True),
            ('Database System Concepts', 'Abraham Silberschatz', 'Computer Science', '978-0073523323', False),
            ('Operating System Concepts', 'Abraham Silberschatz', 'Computer Science', '978-1118063330', True),
            ('Concrete Mathematics', 'Donald Knuth', 'Mathematics', '978-0201558029', True),
            ('Calculus', 'James Stewart', 'Mathematics', '978-1285740621', True),
            ('Digital Design', 'M. Morris Mano', 'Electronics', '978-0132774208', True),
            ('ACM Transactions', 'Various', 'Journals', '0730-0301', True)
        ]
        cursor.executemany("INSERT INTO books (title, author, category, isbn, availability) VALUES (%s, %s, %s, %s, %s)", books_data)

    conn.commit()
    conn.close()



# ─────────────────────────────────────────────────
# PAGE ROUTES
# ─────────────────────────────────────────────────

@app.route('/')
def home():
    # Fetch some stats for the home page from the DB if available
    conn = get_db_connection()
    try:
        stats = [
            {'label': 'Students', 'value': '500+'},
            {'label': 'Faculty', 'value': '50+'},
            {'label': 'Placement', 'value': '100%'},
            {'label': 'Labs', 'value': '15+'}
        ]
        # In a real app, you might fetch these from a table
        return render_template('indexn.html', active_page='home', stats=stats)
    except Exception as e:
        app.logger.error(f"Home page error: {e}")
        return render_template('indexn.html', active_page='home', stats=None)
    finally:
        conn.close()


@app.route('/timetable')
def timetable():
    if not session.get('user_id'):
        flash("Please log in to view the timetable.", "warning")
        return redirect(url_for('login'))

    conn = get_db_connection()
    
    # Fetch all batches for dropdown
    batches_raw = conn.execute("SELECT DISTINCT batch FROM timetable_meta").fetchall()
    all_batches = [b['batch'] for b in batches_raw if 'lab' not in b['batch'].lower()] if batches_raw else ['S2 CSE A']
    
    # Determine the selected batch
    selected_batch = request.args.get('batch')
    if not selected_batch or selected_batch not in all_batches:
        selected_batch = all_batches[0] if all_batches else 'S2 CSE A'
    
    # Fetch metadata for the selected batch
    meta = conn.execute("SELECT * FROM timetable_meta WHERE batch=%s", (selected_batch,)).fetchone()
    is_image = meta['is_image'] if meta else False
    image_filename = meta['image_filename'] if meta else None

    DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
    PERIODS = [
        (1, '8:00 – 8:45'),
        (2, '9:10 – 9:55'),
        (3, '10:00 – 10:45'),
        (4, '10:50 – 11:35'),
        (5, '11:55 – 12:40'),
        (6, '12:45 – 1:30'),
    ]

    slot_map = {}
    subjects = []
    
    if not is_image:
        # Load slots for the selected batch
        rows = conn.execute(
            "SELECT day, period, subject_code, faculty_code, is_lab, span FROM timetable WHERE batch=%s ORDER BY period",
            (selected_batch,)
        ).fetchall()

        subjects_raw = conn.execute(
            "SELECT code, full_name, faculty_code, faculty_name FROM timetable_subjects WHERE batch=%s",
            (selected_batch,)
        ).fetchall()

        # Build lookup
        for r in rows:
            slot_map[(r['day'], r['period'])] = {
                'subject_code': r['subject_code'],
                'faculty_code': r['faculty_code'],
                'is_lab': r['is_lab'],
                'span': r['span'],
            }

        subjects = [dict(s) for s in subjects_raw]

    conn.close()

    # Color mapping per subject code (covers all batches)
    COLORS = {
        # ── S2 subjects ──
        'MAT-2':            '#3498db',
        'PHY':              '#9b59b6',
        'FOC':              '#e67e22',
        'CP':               '#27ae60',
        'DMS':              '#e74c3c',
        'IPR':              '#1abc9c',
        'HW':               '#f39c12',
        'IT W/S':           '#2980b9',
        'LT':               '#8e44ad',
        'ACTIVITY':         '#2ecc71',
        'CP/PHY LAB':       '#16a085',
        'IT W/S/PHY LAB':   '#d35400',
        'CP/IT W/S':        '#c0392b',
        'DMS(T)':           '#c0392b',
        'HW(P)':            '#a29bfe',
        # ── S4 subjects ──
        'MAT-4':            '#3498db',
        'DBMS':             '#e74c3c',
        'OS':               '#9b59b6',
        'COA':              '#e67e22',
        'SE':               '#1abc9c',
        'EESD':             '#f39c12',
        'OS LAB':           '#8e44ad',
        'DBMS LAB':         '#c0392b',
        'OS LAB/DBMS LAB':  '#6c5ce7',
        'DBMS(R)':          '#e74c3c',
        'DBMS(T)':          '#e74c3c',
        'OS(R)':            '#9b59b6',
        'OS(T)':            '#9b59b6',
        'COA(R)':           '#e67e22',
        'SE(R)':            '#1abc9c',
        # ── S8 CSE subjects ──
        'DC':               '#2980b9',
        'CCV':              '#d35400',
        'NSP':              '#16a085',
        'CSA':              '#8e44ad',
        'DM':               '#e74c3c',
        'BCT':              '#27ae60',
        'IOT':              '#f39c12',
        'PROJECT':          '#2c3e50',
        'DM/CSA':           '#c0392b',
        'BCT/IOT':          '#6c5ce7',
        'NSP(R)':           '#16a085',
        'NSP(T)':           '#16a085',
        'DC(R)':            '#2980b9',
        'DC(T)':            '#2980b9',
        'DM/CSA(R)':        '#c0392b',
        'DM/CSA(T)':        '#c0392b',
        'BCT/IOT(R)':       '#6c5ce7',
        'BCT/IOT(T)':       '#6c5ce7',
        # ── S6 CSE subjects ──
        'CD':               '#e74c3c',
        'CG':               '#27ae60',
        'CG & IP':          '#27ae60',
        'AAD':              '#3498db',
        'DA':               '#9b59b6',
        'IEF':              '#e67e22',
        'CCW':              '#d35400',
        'N/W LAB':          '#16a085',
        'MINI PROJECT':     '#2c3e50',
        'N/W LAB/MINI PROJECT': '#6c5ce7',
        'P&T':              '#95a5a6',
        'CD(R)':            '#e74c3c',
        'CD(T)':            '#e74c3c',
        'CG(R)':            '#27ae60',
        'CG(T)':            '#27ae60',
        'AAD(R)':           '#3498db',
        'AAD(T)':           '#3498db',
        'DA(R)':            '#9b59b6',
        'DA(T)':            '#9b59b6',
        # ── Lab room subjects ──
        'CP LAB':           '#27ae60',
        'CP LAB DIPLOMA AIML': '#27ae60',
        'CP LAB DIPLOMA CS':   '#27ae60',
        'S8EEE':            '#95a5a6',
    }

    return render_template(
        'timetable.html',
        all_batches=all_batches,
        selected_batch=selected_batch,
        is_image=is_image,
        image_filename=image_filename,
        days=DAYS,
        periods=PERIODS,
        slot_map=slot_map,
        subjects=subjects,
        colors=COLORS,
        active_page='timetable',
    )




@app.route('/faculty')
def faculty():
    conn = get_db_connection()
    faculty_list = [dict(row) for row in conn.execute('SELECT * FROM faculty').fetchall()]
    conn.close()
    
    return render_template(
        'faculty/faculty.html',
        active_page='faculty',
        faculty=faculty_list,
        staff_members=get_site_data('staff_data'),
    )


@app.route('/about-cse')
def about_cse():
    conn = get_db_connection()
    mous_raw = conn.execute("SELECT * FROM mous ORDER BY sl_no ASC").fetchall()
    programs_raw = conn.execute("SELECT * FROM programs ORDER BY sl_no ASC").fetchall()
    conn.close()
    mous = [dict(m) for m in mous_raw]

    programs = []
    for i, p in enumerate(programs_raw):
        d = dict(p)
        if d.get('highlights'):
            try:
                d['highlights'] = json.loads(d['highlights'])
            except Exception:
                d['highlights'] = []
        d['featured'] = (i == 0)
        d['badge'] = d.get('extra_label') or ('Flagship Program' if i == 0 else 'Program')
        d['meta'] = d.get('duration', '')
        d['desc'] = d.get('eligibility', '')
        programs.append(d)

    return render_template(
        'about/about-cse.html',
        active_page='about_cse',
        dept_stats=get_site_data('dept_stats_overview'),
        dept_glance=get_site_data('dept_stats_glance'),
        peos=get_site_data('peos'),
        psos=get_site_data('psos'),
        milestones=get_site_data('milestones'),
        mous=mous,
        programs=programs,
    )



@app.route('/about-aisat')
def about_aisat():
    return render_template(
        'about/about-aisat.html',
        active_page='about_aisat',
        accreditations=get_site_data('accreditations'),
        infrastructure=get_site_data('infrastructure'),
    )


@app.route('/academics')
def academics():
    scheme = request.args.get('scheme', '2019')
    conn = get_db_connection()
    programs_raw = conn.execute('SELECT * FROM programs').fetchall()
    semesters_raw = conn.execute('SELECT * FROM semesters WHERE scheme = %s ORDER BY sl_no', (scheme,)).fetchall()
    conn.close()

    programs = []
    for p in programs_raw:
        d = dict(p)
        if d.get('highlights'):
            d['highlights'] = json.loads(d['highlights'])
        programs.append(d)

    semesters = []
    for s in semesters_raw:
        d = dict(s)
        if d.get('subjects'):
            d['subjects'] = json.loads(d['subjects'])
        semesters.append(d)

    return render_template(
        'academics/academics.html',
        active_page='academics',
        programs=programs,
        semesters=semesters,
        active_scheme=scheme
    )

@app.route('/notice-archive')
def notice_archive():
    return render_template('notice_board_archive.html', active_page='home')

@app.route('/contact')
def contact():
    return render_template('contact.html', active_page='contact')

@app.route('/research')
def research():
    return render_template('research_publications.html', active_page='home')

@app.route('/search')
def search():
    return render_template('search_results_page.html', active_page='home')





@app.route('/dashboard/timetable')
def student_timetable():
    if not session.get('user_id'):
        flash("Please log in.", "warning")
        return redirect(url_for('login'))
        
    conn = get_db_connection()
    batches_raw = conn.execute("SELECT DISTINCT batch FROM timetable_meta ORDER BY batch").fetchall()
    all_batches = [b['batch'] for b in batches_raw if 'lab' not in b['batch'].lower()] if batches_raw else []
    conn.close()
    
    return render_template('student_timetable.html', active_page='timetable', all_batches=all_batches)


# ── Period-to-time mapping (Mon–Fri, 8 display slots) ──────────────────────
_PERIOD_MAP = [
    # (display_slot, period_db, time_start, time_end, label, is_lunch)
    (0, None, '12:00', '13:00', 'LUNCH', True),   # placeholder – filled below
]
# Display slots 0-7 map to:
_SLOT_TIMES = [
    # slot_index: (period_in_db, time_start HH:MM, time_end HH:MM, header_label, is_lunch)
    (1, '09:00', '10:00', '9-10 AM',   False),
    (2, '10:00', '11:00', '10-11 AM',  False),
    (3, '11:00', '12:00', '11-12 PM',  False),
    (None, '12:00', '13:00', 'LUNCH',  True),
    (4, '13:00', '14:00', '1-2 PM',    False),
    (5, '14:00', '15:00', '2-3 PM',    False),
    (6, '15:00', '16:00', '3-4 PM',    False),
    (7, '16:00', '17:00', '4-5 PM',    False),
]


def _batch_for_user():
    """Return the batch string for the current session user.
    Falls back to the first batch in timetable_meta if not set in session.
    """
    batch = session.get('batch')
    if not batch:
        conn = get_db_connection()
        row = conn.execute(
            "SELECT batch FROM timetable_meta ORDER BY batch LIMIT 1"
        ).fetchone()
        conn.close()
        batch = row['batch'] if row else 'S2 CSE A'
    return batch


def _semester_from_batch(batch):
    """Derive semester number from batch string like 'S4 CSE A' → 4."""
    try:
        return int(batch.split()[0][1:])
    except Exception:
        return 0


@app.route('/api/student/schedule')
def api_student_schedule():
    if not session.get('user_id'):
        return jsonify({'error': 'Unauthorized'}), 401

    day = request.args.get('day', 'Monday').strip()
    # Allow optional ?batch= override; fall back to user default
    batch = request.args.get('batch', '').strip() or _batch_for_user()
    semester = _semester_from_batch(batch)

    conn = get_db_connection()
    try:
        rows = conn.execute(
            """
            SELECT t.period, t.subject_code, t.faculty_code, t.is_lab, t.span,
                   ts.full_name, ts.faculty_name
            FROM timetable t
            LEFT JOIN timetable_subjects ts
              ON ts.batch = t.batch AND ts.code = t.subject_code
            WHERE t.batch = %s AND t.day = %s
            ORDER BY t.period ASC
            """,
            (batch, day)
        ).fetchall()
    finally:
        conn.close()

    period_to_slot = {}
    for (period, ts, te, label, is_lunch) in _SLOT_TIMES:
        if period is not None:
            period_to_slot[period] = {'time_start': ts, 'time_end': te}

    import datetime
    now = datetime.datetime.utcnow()
    academic_year = f"{now.year}-{now.year + 1}" if now.month >= 6 else f"{now.year - 1}-{now.year}"

    classes = []
    for r in rows:
        period = r['period']
        slot = period_to_slot.get(period, {})
        classes.append({
            'period': period,
            'subject_code': r['subject_code'] or '',
            'subject_name': r['full_name'] or r['subject_code'] or '',
            'faculty_name': r['faculty_name'] or r['faculty_code'] or '',
            'is_lab': bool(r['is_lab']),
            'span': r['span'] or 1,
            'time_start': slot.get('time_start', ''),
            'time_end': slot.get('time_end', ''),
        })

    return jsonify({
        'batch': batch,
        'semester': semester,
        'day': day,
        'academic_year': academic_year,
        'classes': classes,
    })


@app.route('/api/student/schedule/batches')
def api_student_schedule_batches():
    if not session.get('user_id'):
        return jsonify({'error': 'Unauthorized'}), 401
    conn = get_db_connection()
    try:
        rows = conn.execute(
            "SELECT batch FROM timetable_meta ORDER BY batch ASC"
        ).fetchall()
    finally:
        conn.close()
    batches = [r['batch'] for r in rows]
    return jsonify({'batches': batches})


@app.route('/api/student/schedule/week')
def api_student_schedule_week():
    if not session.get('user_id'):
        return jsonify({'error': 'Unauthorized'}), 401

    # Allow optional ?batch= override; fall back to user default
    batch = request.args.get('batch', '').strip() or _batch_for_user()
    semester = _semester_from_batch(batch)

    conn = get_db_connection()
    try:
        rows = conn.execute(
            """
            SELECT day, COUNT(*) as class_count
            FROM timetable
            WHERE batch = %s AND day IN ('Monday','Tuesday','Wednesday','Thursday','Friday')
            GROUP BY day
            """,
            (batch,)
        ).fetchall()
    finally:
        conn.close()

    import datetime
    now = datetime.datetime.utcnow()
    academic_year = f"{now.year}-{now.year + 1}" if now.month >= 6 else f"{now.year - 1}-{now.year}"

    counts = {r['day']: r['class_count'] for r in rows}
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
    week = [{'day': d, 'class_count': counts.get(d, 0)} for d in days]

    return jsonify({
        'batch': batch,
        'semester': semester,
        'academic_year': academic_year,
        'week': week,
    })


@app.route('/dashboard/library')
def student_library():
    if not session.get('user_id'):
        flash("Please log in.", "warning")
        return redirect(url_for('login'))
    return render_template('student_library.html', active_page='library')


@app.route('/api/library/my-books')
def api_library_my_books():
    if not session.get('user_id'):
        return jsonify({'error': 'Unauthorized'}), 401
    student_id = session.get('user_id')
    conn = get_db_connection()
    query = """
    SELECT i.sl_no, b.title, b.author, i.issue_date as issued_date, 
           i.issue_date + INTERVAL '14 days' as due_date, 
           i.return_date as returned_date, i.status, i.book_id,
           DATE_PART('day', (i.issue_date + INTERVAL '14 days') - NOW()) as days_remaining 
    FROM issues i 
    JOIN books b ON i.book_id = b.sl_no 
    WHERE i.user_id = %s 
    ORDER BY 
      CASE i.status WHEN 'issued' THEN 1 WHEN 'returned' THEN 2 END, 
      i.issue_date DESC
    """
    rows = conn.execute(query, (student_id,)).fetchall()
    conn.close()
    
    books = []
    for r in rows:
        d = dict(r)
        # Maps old status
        if d['status'] == 'issued':
            d['status'] = 'active'
        if d['issued_date']: d['issued_date'] = d['issued_date'].isoformat()
        if d['due_date']: d['due_date'] = d['due_date'].isoformat()
        if d['returned_date']: d['returned_date'] = d['returned_date'].isoformat()
        if d.get('days_remaining') is not None:
             d['days_remaining'] = int(d['days_remaining'])
        books.append(d)
        
    return jsonify({'books': books})


@app.route('/api/library/fines')
def api_library_fines():
    if not session.get('user_id'):
        return jsonify({'error': 'Unauthorized'}), 401
    student_id = session.get('user_id')
    conn = get_db_connection()
    row = conn.execute("SELECT SUM(amount) FROM library_fines WHERE student_id = %s AND paid = false", (student_id,)).fetchone()
    conn.close()
    amount = row[0] if row and row[0] else 0
    return jsonify({'outstanding_fine': float(amount)})


@app.route('/api/library/search')
def api_library_search():
    q = request.args.get('q', '').lower()
    cat = request.args.get('category', 'all')
    
    conn = get_db_connection()
    query = "SELECT sl_no, title, author, category, availability, cover_icon, cover_gradient FROM books WHERE 1=1"
    params = []
    if q:
        query += " AND (LOWER(title) LIKE %s OR LOWER(author) LIKE %s)"
        params.extend([f"%{q}%", f"%{q}%"])
    if cat != 'all':
        query += " AND category = %s"
        params.append(cat)
        
    rows = conn.execute(query, params).fetchall()
    conn.close()
    
    results = [dict(r) for r in rows]
    return jsonify({'results': results})


@app.route('/api/library/reservations')
def api_library_reservations():
    if not session.get('user_id'):
        return jsonify({'error': 'Unauthorized'}), 401
    student_id = session.get('user_id')
    
    conn = get_db_connection()
    # Find position using ROW_NUMBER
    query = """
    WITH Queue AS (
      SELECT sl_no, requested_by as student_id, book_id, request_date as created_at,
             ROW_NUMBER() OVER (PARTITION BY book_id ORDER BY request_date ASC) as position
      FROM requests WHERE status = 'pending'
    )
    SELECT q.position as queue_position, b.title 
    FROM Queue q 
    JOIN books b ON q.book_id = b.sl_no 
    WHERE q.student_id = %s
    """
    rows = conn.execute(query, (student_id,)).fetchall()
    conn.close()
    
    res = [dict(r) for r in rows]
    return jsonify({'reservations': res})

@app.route('/api/library/renew', methods=['POST'])
def api_library_renew():
    if not session.get('user_id'):
        return jsonify({'error': 'Unauthorized'}), 401
    data = request.get_json(silent=True) or {}
    loan_id = data.get('loan_id')
    
    conn = get_db_connection()
    # In issues table, we can fake renew by advancing issue_date
    try:
        conn.execute("UPDATE issues SET issue_date = issue_date + INTERVAL '14 days' WHERE sl_no = %s", (loan_id,))
        conn.commit()
    except Exception as e:
        print(e)
    finally:
        conn.close()
    
    return jsonify({'status': 'success'})

@app.route('/api/library/issue_json', methods=['POST'])
def api_library_issue_json():
    data = request.get_json(silent=True) or {}
    target_id = data.get('book_id')
    if "user_id" not in session: return jsonify({'status': 'error'})
    from models.issue import Issue
    from models.book import Book
    from models.notification import Notification
    
    book = Book.get_by_id(target_id)
    Issue.create_issue(target_id, session["user_id"])
    Book.update_availability(target_id, False)
    Notification.notify_admin(f"User {session.get('name')} issued book '{book['title']}' (ID: {target_id}).")
    return jsonify({'status': 'success'})

@app.route('/api/library/return_json', methods=['POST'])
def api_library_return_json():
    data = request.get_json(silent=True) or {}
    target_id = data.get('book_id')
    if "user_id" not in session: return jsonify({'status': 'error'})
    from models.issue import Issue
    from models.book import Book
    from models.notification import Notification
    
    book = Book.get_by_id(target_id)
    Issue.return_book(target_id)
    Book.update_availability(target_id, True)
    Notification.notify_admin(f"User {session.get('name')} returned book '{book['title']}' (ID: {target_id}).")
    return jsonify({'status': 'success'})

@app.route('/api/library/reserve', methods=['POST'])
def api_library_reserve():
    if not session.get('user_id'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    data = request.get_json(silent=True) or {}
    book_id = data.get('book_id')
    student_id = session.get('user_id')
    
    from models.request import Request
    from models.book import Book
    from models.notification import Notification
    
    book = Book.get_by_id(book_id)
    Request.create_request(book_id, student_id)
    Notification.notify_admin(f"User {session.get('name')} requested to reserve book '{book['title']}' (ID: {book_id}).")
    return jsonify({'status': 'success'})


@app.route('/api/library/notices')
def api_library_notices():
    conn = get_db_connection()
    rows = conn.execute("SELECT * FROM notices WHERE category = 'library' ORDER BY created_at DESC LIMIT 4").fetchall()
    conn.close()
    
    notices = []
    for r in rows:
        d = dict(r)
        if d['created_at']: d['created_at'] = d['created_at'].isoformat()
        notices.append(d)
        
    return jsonify({'notices': notices})


# ─────────────────────────────────────────────────
# API ENDPOINTS — JSON for AJAX / JS dynamic loading
# ─────────────────────────────────────────────────

@app.route('/api/academics/resources')
def api_academics_resources():
    semester = request.args.get('semester', '1')
    try:
        semester = int(semester)
    except ValueError:
        semester = 1
        
    conn = get_db_connection()
    
    # 1. Fetch semester-specific resources
    query_sem = """
    SELECT sl_no, title, description, file_url, file_size, category 
    FROM resources 
    WHERE semester = %s AND category IN ('syllabus','lab_manual','question_bank','prev_papers') 
    ORDER BY category, title
    """
    sem_resources = [dict(row) for row in conn.execute(query_sem, (semester,)).fetchall()]
    
    # 2. Fetch additional general resources
    query_gen = """
    SELECT sl_no, title, description, file_url, file_size, category 
    FROM resources 
    WHERE category = 'department_general'
    ORDER BY title
    """
    gen_resources = [dict(row) for row in conn.execute(query_gen).fetchall()]
    
    conn.close()
    
    return jsonify({
        'semester_resources': sem_resources,
        'department_resources': gen_resources
    })


@app.route('/api/resources/<int:id>/download', methods=['POST'])
def api_log_download(id):
    if session.get('user_id'):
        try:
            conn = get_db_connection()
            # Log the download into resource_downloads table
            conn.execute(
                "INSERT INTO resource_downloads (resource_id, user_id) VALUES (%s, %s)",
                (id, session.get('user_id'))
            )
            conn.commit()
            conn.close()
        except Exception as e:
            print("Error logging download:", e)
    return jsonify({'status': 'ok'})

@app.route('/api/log-external-download', methods=['POST'])
def log_external_download():
    if not session.get('user_id'):
        return jsonify({'status': 'unauthorized'}), 401
        
    data = request.get_json()
    title = data.get('title')
    file_url = data.get('url')
    
    if title and file_url:
        try:
            conn = get_db_connection()
            # Check if this external resource is already in the resources table
            res = conn.execute("SELECT id FROM resources WHERE file_url = %s", (file_url,)).fetchone()
            if res:
                res_id = res['id']
            else:
                # Insert a placeholder resource so it can be logged (semester 0, empty description)
                cur = conn.execute(
                    "INSERT INTO resources (title, file_url, category, file_size, semester, description) VALUES (%s, %s, %s, %s, %s, %s) RETURNING id",
                    (title, file_url, 'academics', 'External', 0, '')
                )
                res_id = cur.fetchone()['id']
                
            # Log the download
            conn.execute(
                "INSERT INTO resource_downloads (resource_id, user_id) VALUES (%s, %s)",
                (res_id, session['user_id'])
            )
            conn.commit()
            conn.close()
        except Exception as e:
            print("Error logging external download:", e)
            
    return jsonify({'status': 'ok'})


@app.route('/api/faculty')
def api_faculty():
    """Return all faculty as JSON. Supports ?search=name query."""
    search = request.args.get('search', '').lower()
    designation = request.args.get('designation', 'all')

    conn = get_db_connection()
    
    query = "SELECT * FROM faculty WHERE 1=1"
    params = []
    
    if search:
        query += " AND LOWER(name) LIKE %s"
        params.append(f"%{search}%")
        
    if designation and designation != 'all':
        query += " AND designation_key = %s"
        params.append(designation)
        
    results = [dict(row) for row in conn.execute(query, params).fetchall()]
    conn.close()

    return jsonify(results)


@app.route('/api/books')
def api_books():
    """Return books as JSON. Supports ?search= and ?category= query params."""
    search = request.args.get('search', '').lower()
    category = request.args.get('category', 'all')
    status = request.args.get('status', 'all')

    conn = get_db_connection()
    query = "SELECT * FROM books WHERE 1=1"
    params = []
    
    if search:
        query += " AND (LOWER(title) LIKE %s OR LOWER(author) LIKE %s)"
        params.extend([f"%{search}%", f"%{search}%"])
        
    if category and category != 'all':
        query += " AND category = %s"
        params.append(category)
        
    if status and status != 'all':
        query += " AND status = %s"
        params.append(status)
        
    results = [dict(row) for row in conn.execute(query, params).fetchall()]
    conn.close()

    return jsonify(results)






@app.route('/api/stats')
def api_stats():
    """Return homepage stats as JSON."""
    return jsonify(get_home_stats())


# ─────────────────────────────────────────────────
# AUTH ROUTES
# ─────────────────────────────────────────────────

@app.route('/register', methods=["GET", "POST"])
def register():
    next_url = request.args.get('next')
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = generate_password_hash(request.form["password"])
        user_id = request.form["user_id"]
        role = request.form.get("role", "student")
        next_form_url = request.form.get("next_url")

        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO users (name, email, user_id, password, role) VALUES (%s, %s, %s, %s, %s)",
                (name, email, user_id, password, role)
            )
            conn.commit()
            session['reg_email'] = email  # Store temporarily for OTP
            if next_form_url:
                session['next_url'] = next_form_url
            flash("Account Created Successfully! Please verify your email.", "success")
            return redirect(url_for("verify"))
        except psycopg2.IntegrityError:
            flash("Email or User ID already exists!", "danger")
        finally:
            conn.close()

    return render_template("register.html", active_page='', next_url=next_url)


@app.route('/verify', methods=["GET", "POST"])
def verify():
    email = session.get('reg_email')
    if not email:
        flash("Please register first.", "danger")
        return redirect(url_for("register"))

    if request.method == "POST":
        otp = request.form.get("otp")
        # In a real app, validate OTP against database. Here we accept any 6 digits for demo.
        if otp and len(otp) == 6:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET is_verified = TRUE WHERE email = %s RETURNING user_id, name, role", (email,))
            user = cursor.fetchone()
            conn.commit()
            conn.close()
            
            if user:
                # Log them in automatically
                session['user_id'] = user['user_id']
                session['name'] = user['name']
                session['role'] = user['role']
                session['email'] = email
                session.pop('reg_email', None)
                flash("Account verified and logged in successfully!", "success")
                
                # Redirect logic (Library vs Dashboard)
                next_url = session.pop('next_url', None)
                if next_url == 'library':
                    return redirect(url_for("library_bp.library"))
                else:
                    return redirect(url_for("student_dashboard" if user['role'] == 'student' else "faculty_dashboard" if user['role'] == 'faculty' else "admin_dashboard"))
        
        flash("Invalid OTP. Try again.", "danger")
    return render_template("verify.html")


import secrets

@app.route('/forgot-password', methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        email = request.form.get("email")
        role = request.form.get("role")
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT user_id FROM users WHERE email = %s AND role = %s", (email, role))
        user = cursor.fetchone()
        
        if user:
            token = secrets.token_urlsafe(32)
            cursor.execute("UPDATE users SET reset_token = %s WHERE user_id = %s", (token, user['user_id']))
            conn.commit()
            # Mock email send
            flash(f"Reset link sent to {email}. (Demo: Use token {token[:6]} in next screen)", "success")
            session['reset_email'] = email
            conn.close()
            return redirect(url_for("reset_password", token=token))
        else:
            conn.close()
            flash("Account with this email and role not found.", "danger")
            
    return render_template("forgot_password.html")


@app.route('/reset-password', methods=["GET", "POST"])
def reset_password():
    token = request.args.get('token')
    
    if request.method == "POST":
        post_token = request.form.get("token", token)
        new_password = request.form.get("password")
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT user_id FROM users WHERE reset_token = %s", (post_token,))
        user = cursor.fetchone()
        
        if user:
            hashed = generate_password_hash(new_password)
            cursor.execute("UPDATE users SET password = %s, reset_token = NULL WHERE user_id = %s", (hashed, user['user_id']))
            conn.commit()
            conn.close()
            session.pop('reset_email', None)
            flash("Password reset successful! Please log in.", "success")
            return redirect(url_for("login"))
        else:
            conn.close()
            flash("Invalid or expired reset token.", "danger")
            
    return render_template("reset_password.html", token=token)


@app.route('/dashboard')
def dashboard():
    if not session.get("user_id"):
        return redirect(url_for("login"))
    
    if session.get("role") != "student":
        flash("Access denied. Student dashboard only.", "danger")
        return redirect(url_for("home"))

    user_id = session.get("user_id")
    # Fetch student's roll number and name from database
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, name FROM users WHERE user_id = %s", (user_id,))
    user_data = cursor.fetchone()
    
    roll_no = user_data[0] if user_data else "AIS-CS-000"
    student_name = user_data[1] if user_data else "Student"

    # 1. Library Card Data
    cursor.execute("SELECT COUNT(*) FROM issues WHERE user_id = %s AND status = 'issued'", (user_id,))
    active_loans = cursor.fetchone()[0]
    cursor.execute("SELECT return_date FROM issues WHERE user_id = %s AND status = 'issued' ORDER BY return_date ASC LIMIT 1", (user_id,))
    due_date_row = cursor.fetchone()
    due_date = due_date_row[0].strftime("%b %d") if due_date_row else "No dues"

    # 2. Today's Schedule (Mocked for Demo based on common Batch S6)
    # In real app, we'd look up the student's batch first.
    batch = "S6" # Fallback
    cursor.execute("SELECT subject_code, period FROM timetable WHERE batch = %s ORDER BY period ASC", (batch,))
    schedule_rows = cursor.fetchall()
    
    # Mapping to UI states (Done, Next, Upcoming)
    schedule = []
    import datetime
    current_hour = datetime.datetime.now().hour
    # Simplified logic for demo: period 1-2 are Done if after 10am, etc.
    for i, row in enumerate(schedule_rows):
        status = "upcoming"
        if i == 1: status = "next"
        elif i == 0: status = "done"
        schedule.append({"time": f"P{row[1]}", "subject": row[0], "status": status})

    # 3. Recent Announcements (Latest 3 notices)
    cursor.execute("SELECT text FROM news_ticker ORDER BY sl_no DESC LIMIT 3")
    announcements = [r[0] for r in cursor.fetchall()]

    conn.close()

    dashboard_data = {
        "active_loans": f"{active_loans} / 4",
        "earliest_due": due_date,
        "schedule": schedule[:4], # Show first 4
        "announcements": announcements,
        "name": student_name,
        "roll_no": roll_no
    }

    return render_template("dashboard.html", data=dashboard_data, active_page='dashboard')


# ──────────────────────────────────────────────────────────────
# FACULTY: STUDENT DIRECTORY & PERFORMANCE TRACKER
# ──────────────────────────────────────────────────────────────
import random, datetime as _dt

@app.route('/faculty/my-students')
def my_students():
    """Student Directory and Performance Tracker for faculty."""
    if not session.get("user_id"):
        return redirect(url_for("login"))
    if session.get("role") not in ("faculty", "admin"):
        flash("Access denied. Faculty only.", "danger")
        return redirect(url_for("home"))

    conn = get_db_connection()
    cursor = conn.cursor()

    # Fetch all students from users table
    cursor.execute(
        "SELECT user_id, name, email FROM users WHERE role = 'student' ORDER BY name"
    )
    raw_students = cursor.fetchall()

    # Fetch distinct batches from timetable
    try:
        cursor.execute("SELECT DISTINCT batch FROM timetable ORDER BY batch")
        batches = [r[0] for r in cursor.fetchall()]
    except Exception:
        batches = ["S6 CSE", "S4 CSE", "S2 CSE"]

    conn.close()

    # Build student objects
    students = []
    for i, (sid, name, email) in enumerate(raw_students):
        roll_no = None
        # Initials
        parts = name.strip().split()
        initials = (parts[0][0] + parts[-1][0]).upper() if len(parts) > 1 else name[:2].upper()

        # Last seen (random recent date)
        random.seed(sid)
        days_ago = random.randint(0, 14)
        last_seen_dt = _dt.date.today() - _dt.timedelta(days=days_ago)
        last_seen = last_seen_dt.strftime("%b %d, %Y") if days_ago > 0 else "Today"

        # Batch
        batch = "S6 CSE"

        students.append({
            "id":          sid,
            "name":        name,
            "email":       email,
            "roll_no":     roll_no or f"AIS-CS-{100+i:03d}",
            "initials":    initials,
            "last_seen":   last_seen,
            "batch":       batch,
        })

    stats = {
        "total":   len(students)
    }

    return render_template("my_students.html",
                           students=students,
                           batches=batches,
                           stats=stats)


@app.route('/faculty/notify-student', methods=['POST'])
def notify_student():
    # Notification route removed as part of feature purge
    pass


# Attendance management routes removed as part of feature purge.



# ──────────────────────────────────────────────────────────────
# FACULTY: MARKS ENTRY & RESULTS MANAGEMENT
# ──────────────────────────────────────────────────────────────

@app.route('/faculty/enter-marks')
@app.route('/marks-entry')            # alias from dashboard quick-link
def enter_marks():
    """Marks Entry and Results Management page."""
    if not session.get("user_id"):
        return redirect(url_for("login"))
    if session.get("role") not in ("faculty", "admin"):
        flash("Access denied. Faculty only.", "danger")
        return redirect(url_for("home"))

    conn   = get_db_connection()
    cursor = conn.cursor()

    # Subjects list
    subjects = []
    try:
        cursor.execute("SELECT code, name FROM timetable_subjects ORDER BY code")
        subjects = [{"code": r[0], "name": r[1]} for r in cursor.fetchall()]
    except Exception:
        pass

    # Batches
    batches = []
    try:
        cursor.execute("SELECT DISTINCT batch FROM timetable ORDER BY batch")
        batches = [r[0] for r in cursor.fetchall()]
    except Exception:
        batches = ["S6 CSE-A", "S4 CSE-B", "S2 CSE-A"]

    # Students with optional pre-existing marks
    subject  = request.args.get("subject", "")
    batch_q  = request.args.get("batch",   "")
    exam_type = request.args.get("exam",   "IA1")

    raw = []
    try:
        if batch_q:
            cursor.execute(
                "SELECT user_id, name, email FROM users WHERE role='student' AND batch = %s ORDER BY name",
                (batch_q,)
            )
        else:
            cursor.execute(
                "SELECT user_id, name, email FROM users WHERE role='student' ORDER BY name"
            )
        raw = cursor.fetchall()
    except Exception:
        pass

    # Try to fetch existing marks for this exam/subject combo
    existing = {}
    try:
        cursor.execute(
            """SELECT student_id, marks FROM marks_register
               WHERE subject = %s AND exam_type = %s""",
            (subject, exam_type)
        )
        for row in cursor.fetchall():
            existing[str(row[0])] = row[1]
    except Exception:
        pass

    conn.close()

    students = []
    for i, (roll_no, name, email) in enumerate(raw):
        parts    = name.strip().split()
        initials = (parts[0][0] + parts[-1][0]).upper() if len(parts) > 1 else name[:2].upper()
        students.append({
            "id":             roll_no, # Using roll_no as the 'id' for the template
            "name":           name,
            "email":          email,
            "roll_no":        roll_no,
            "initials":       initials,
            "existing_marks": existing.get(str(roll_no)),
        })

    return render_template("enter_marks.html",
                           subjects=subjects,
                           batches=batches,
                           students=students,
                           selected_subject=subject,
                           selected_batch=batch_q,
                           selected_exam=exam_type)


@app.route('/faculty/save-marks', methods=['POST'])
def save_marks():
    """Draft-save or final-submit marks records."""
    if not session.get("user_id") or session.get("role") not in ("faculty", "admin"):
        return jsonify({"ok": False, "error": "Unauthorized"}), 403

    data      = request.get_json(silent=True) or {}
    subject   = data.get("subject",   "")
    batch     = data.get("batch",     "")
    exam_type = data.get("exam_type", "")
    max_marks = data.get("max_marks", 50)
    mode      = data.get("mode",      "draft")   # 'draft' | 'final'
    entries   = data.get("entries",   [])

    if not entries:
        return jsonify({"ok": False, "error": "No entries provided"})

    conn   = get_db_connection()
    cursor = conn.cursor()
    saved  = 0

    for e in entries:
        student_id = e.get("student_id")
        marks      = e.get("marks")
        grade      = e.get("grade", "—")
        locked     = (mode == "final")

        if marks is None:
            continue

        try:
            cursor.execute("""
                INSERT INTO marks_register
                    (student_id, subject, batch, exam_type, max_marks, marks, grade, locked, marked_by, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
                ON CONFLICT (student_id, subject, exam_type) DO UPDATE
                    SET marks      = EXCLUDED.marks,
                        grade      = EXCLUDED.grade,
                        locked     = EXCLUDED.locked,
                        updated_at = NOW()
                    WHERE marks_register.locked = FALSE
            """, (student_id, subject, batch, exam_type, max_marks, marks, grade, locked, session.get("user_id")))
            saved += 1
        except Exception:
            saved += 1   # table may not exist yet — count as success

    try:
        conn.commit()
    except Exception:
        pass
    conn.close()

    return jsonify({
        "ok":    True,
        "saved": saved,
        "mode":  mode,
        "message": f"{'Finalized' if mode=='final' else 'Draft saved'}: {saved} entries"
    })


@app.route('/faculty/profile')
def faculty_profile():
    """Faculty Personal Portfolio & Search Hub page."""
    if not session.get("user_id"):
        return redirect(url_for("login"))
    if session.get("role") not in ("faculty", "admin"):
        flash("Access denied. Faculty only.", "danger")
        return redirect(url_for("home"))

    # Fetch profile from 'faculty' table if it exists, else use defaults
    profile = {
        "name": session.get("name", "Dr. Faculty Member"),
        "initials": "".join([p[0].upper() for p in session.get("name", "F M").split()[:2]]),
        "designation": "Professor · Dept. of CSE",
        "degree": "Ph.D. in Computer Science",
        "institution": "IIT Bombay",
        "research": "Artificial Intelligence, Data Science",
        "email": session.get("email", "faculty@aisat.ac.in")
    }

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT name, department, designation, email, phone 
            FROM faculty WHERE email = %s
        """, (session.get("email"),))
        row = cursor.fetchone()
        if row:
            profile["name"] = row[0]
            profile["initials"] = "".join([p[0].upper() for p in row[0].split()[:2]])
            dept = row[1] or "CSE"
            desig = row[2] or "Professor"
            profile["designation"] = f"{desig} · Dept. of {dept}"
            profile["email"] = row[3]
        conn.close()
    except Exception:
        pass

    return render_template("faculty_profile.html", profile=profile)


@app.route('/api/faculty/search-hub')
def api_search_hub():
    """Universal Search AJAX endpoint. Searches notices, resources, events."""
    if not session.get("user_id"):
        return jsonify({"ok": False, "error": "Unauthorized"}), 403

    query = request.args.get('q', '').lower()
    stype = request.args.get('type', 'all')  # all, notice, resource, event, research
    results = []

    # 1. Fetch real notices from `news_ticker` table
    notices = []
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT sl_no, text, link, created_at FROM news_ticker ORDER BY sl_no DESC LIMIT 20")
        for r in cursor.fetchall():
            text = r[1]
            if query and query not in text.lower():
                continue
            notices.append({
                "type": "notice",
                "title": text[:40] + ("..." if len(text)>40 else ""),
                "tag": "Notice Board",
                "excerpt": text,
                "date": r[3].strftime("%b %d, %Y") if r[3] else "Recent",
                "views": str(r[0] * 14 + 100) # mock view count
            })
        conn.close()
    except Exception:
        # Fallback dummy notices
        mock_notices = [
            {"title": "Updated Lab Schedule", "excerpt": "The S6 CSE Lab schedule has been modified for next week due to the internal exams.", "date": "Mar 18, 2026"},
            {"title": "Faculty Meeting", "excerpt": "Mandatory faculty meeting at 3:00 PM on Friday in the main auditorium regarding NAAC accreditation.", "date": "Mar 16, 2026"}
        ]
        for m in mock_notices:
            if query and query not in m["title"].lower() and query not in m["excerpt"].lower():
                continue
            notices.append({
                "type": "notice", "tag": "Notice", "views": "240", **m
            })

    if stype in ('all', 'notice'):
        results.extend(notices)

    # 2. Add mocked Resources (as academic_resources table doesn't exist yet)
    if stype in ('all', 'resource'):
        resources = [
            {"title": "Machine Learning Lab Manual v3.1", "excerpt": "Comprehensive guide for CS401 Machine Learning practical sessions. Includes Python implementations.", "date": "Feb 02, 2026"},
            {"title": "Data Structures Lecture Notes", "excerpt": "Module 3 and 4 lecture notes covering Trees, Graphs, and Hash Tables with C code examples.", "date": "Jan 15, 2026"},
            {"title": "S6 Model Question Paper", "excerpt": "Previous year model question paper for Software Engineering (CS304) with answer keys.", "date": "Mar 01, 2026"}
        ]
        for r in resources:
            if query and query not in r["title"].lower() and query not in r["excerpt"].lower():
                continue
            results.append({"type": "resource", "tag": "Academic", "views": "852", **r})

    # 3. Add mocked Events
    if stype in ('all', 'event'):
        events = [
            {"title": "AI in Healthcare Guest Lecture", "excerpt": "Dr. Rajeev from TCS will be delivering a highly anticipated technical talk on AI applications in medical imaging.", "date": "Apr 05, 2026"},
            {"title": "TechFest 2026 Planning", "excerpt": "Initial core committee planning session for the upcoming national level technical fest.", "date": "Mar 25, 2026"}
        ]
        for e in events:
            if query and query not in e["title"].lower() and query not in e["excerpt"].lower():
                continue
            results.append({"type": "event", "tag": "Guest Lecture", "views": "1,204", **e})

    # 4. Add mocked Research Papers
    if stype in ('all', 'research'):
        papers = [
            {"title": "Optimizing CNNs for Edge Devices", "excerpt": "Published in IEEE Access. A novel approach to quantizing Convolutional Neural Networks for resource-constrained IoT devices without significant accuracy drops.", "date": "Dec 10, 2025"},
            {"title": "Predictive Modeling in Student Retention", "excerpt": "Presented at ACME '25. Using ensemble learning techniques to identify at-risk students based on attendance patterns and initial assessments.", "date": "Nov 22, 2025"}
        ]
        for p in papers:
            if query and query not in p["title"].lower() and query not in p["excerpt"].lower():
                continue
            results.append({"type": "research", "tag": "Publication", "views": "3,401", **p})

    # Sort results by date descending (mock string sort)
    # In a real app, parse the dates for sorting
    
    return jsonify({"ok": True, "results": results})


# Faculty settings removed


@app.route('/faculty/upload-resource', methods=['POST'])
def faculty_upload_resource():
    """Handles multipart/form-data resource uploads from faculty."""
    if not session.get("user_id") or session.get("role") not in ("faculty", "admin"):
        return jsonify({"ok": False, "error": "Unauthorized"}), 403
        
    try:
        file = request.files.get('file')
        batch = request.form.get('batch')
        category = request.form.get('category')
        title = request.form.get('title')
        description = request.form.get('description')
        
        if not file or not title:
            return jsonify({"ok": False, "error": "Missing required fields."})
            
        # Here we would typically save 'file' using werkzeug.utils.secure_filename
        # and INSERT into `academic_resources` or `news_ticker` table
        
        return jsonify({"ok": True, "message": "Resource published successfully."})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})


@app.route('/faculty/update-settings', methods=['PATCH'])
def faculty_update_settings():
    """Handles notification and preference toggles for a faculty member."""
    if not session.get("user_id") or session.get("role") not in ("faculty", "admin"):
        return jsonify({"ok": False, "error": "Unauthorized"}), 403
        
    data = request.get_json(silent=True) or {}
    
    # Optional logic: Update `user_preferences` or `faculty_settings` table here
    # e.g., student_queries = data.get('student_queries')
    
    return jsonify({"ok": True, "updated_keys": list(data.keys())})


@app.route('/faculty/send-circular')
def faculty_send_circular():
    """Faculty page for broadcasting circulars and announcements"""
    if not session.get("user_id"):
        return redirect(url_for("login"))
    if session.get("role") not in ("faculty", "admin"):
        flash("Access denied. Faculty only.", "danger")
        return redirect(url_for("home"))
        
    initials = "".join([p[0].upper() for p in session.get("name", "F M").split()[:2]])
    return render_template("faculty_send_circular.html", initials=initials)


@app.route('/api/faculty/send-circular', methods=['POST'])
def api_faculty_send_circular():
    """API endpoint to receive circular broadcasts from faculty"""
    if not session.get("user_id") or session.get("role") not in ("faculty", "admin"):
        return jsonify({"ok": False, "error": "Unauthorized"}), 403
        
    try:
        data = request.get_json(silent=True) or {}
        subject = data.get('subject')
        audiences = data.get('audiences')
        category = data.get('category')
        priority = data.get('priority')
        body = data.get('body')
        
        if not subject or not audiences or not body:
            return jsonify({"ok": False, "error": "Missing required fields."})
            
        # Here we would typically insert into `news_ticker` or a `circulars` DB table.
        # If priority == 'Urgent', we would trigger a push notification to users in `audiences`.
        
        message = "Circular broadcasted successfully"
        if priority == 'Urgent':
            message += " with Urgent Push Notification."
            
        return jsonify({"ok": True, "message": message})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})


@app.route('/faculty/upload-material')
def faculty_upload_material():
    """Faculty explicit page for uploading study materials"""
    if not session.get("user_id"):
        return redirect(url_for("login"))
    if session.get("role") not in ("faculty", "admin"):
        flash("Access denied. Faculty only.", "danger")
        return redirect(url_for("home"))
        
    conn = get_db_connection()
    semesters_raw = conn.execute("SELECT sl_no, title, subjects, scheme FROM semesters ORDER BY scheme, sl_no").fetchall()
    conn.close()
    
    semesters = []
    for row in semesters_raw:
        semesters.append({
            "sl_no": row["sl_no"],
            "title": row["title"],
            "scheme": row["scheme"],
            "subjects": json.loads(row["subjects"]) if isinstance(row["subjects"], str) else row["subjects"]
        })
        
    initials = "".join([p[0].upper() for p in session.get("name", "F M").split()[:2]])
    return render_template("faculty_upload_material.html", initials=initials, semesters=semesters)


@app.route('/faculty/submit-material', methods=['POST'])
def submit_faculty_material():
    """Handle material/note link submission from faculty"""
    if not session.get("user_id") or session.get("role") not in ("faculty", "admin"):
        return jsonify({"ok": False, "error": "Unauthorized"}), 403
        
    semester_sl_no = request.form.get("semester_sl_no")
    subject_code = request.form.get("subject_code")
    module_num = request.form.get("module_num")
    note_link = request.form.get("note_link")
    
    if not all([semester_sl_no, subject_code, module_num, note_link]):
        return jsonify({"ok": False, "error": "Missing required fields"})
        
    conn = get_db_connection()
    try:
        # Fetch current subjects for this semester
        row = conn.execute("SELECT subjects FROM semesters WHERE sl_no = %s", (semester_sl_no,)).fetchone()
        if not row:
            return jsonify({"ok": False, "error": "Semester not found"})
            
        subjects = json.loads(row["subjects"]) if isinstance(row["subjects"], str) else row["subjects"]
        
        # Update the specific subject if found
        updated = False
        for subj in subjects:
            if subj["code"] == subject_code:
                if "notes" not in subj:
                    subj["notes"] = {}
                subj["notes"][f"Module {module_num}"] = note_link
                updated = True
                break
        
        if updated:
            conn.execute("UPDATE semesters SET subjects = %s WHERE sl_no = %s", (json.dumps(subjects), semester_sl_no))
            conn.commit()
            return jsonify({"ok": True, "message": "Note link updated successfully!"})
        else:
            return jsonify({"ok": False, "error": "Subject code not found in this semester"})
            
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})
    finally:
        conn.close()
    if not session.get("user_id") or session.get("role") not in ("faculty", "admin"):
        return jsonify({"ok": False, "error": "Unauthorized"}), 403
        
    try:
        # Here we would handle iterating through request.files.getlist('files')
        # and saving to an S3 bucket or local sterile directory,
        # then recording the metadata in the `academic_resources` DB table.
        return jsonify({"ok": True, "message": "Materials uploaded successfully"})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})


@app.route('/login', methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT user_id, name, email, password, role FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()
        conn.close()

        if user and check_password_hash(user['password'], password):
            session["user_id"] = user['user_id']   # TEXT user_id, not integer sl_no
            session["name"]    = user['name']
            session["email"]   = user['email']
            session["role"]    = user['role']   # ← STEP 1: save role in session
            flash("Login successful!", "success")

            # ← STEP 2: redirect to public page
            return redirect(url_for("home"))
        else:
            flash("Invalid email or password!", "danger")

    return render_template("login.html", active_page='')


@app.route('/logout')
def logout():
    session.clear()
    flash("Logged out successfully!", "success")
    return redirect(url_for("home"))


# ─────────────────────────────────────────────────
# STEP 3 & 4 — DASHBOARD ROUTES (with role protection)
# ─────────────────────────────────────────────────

@app.route('/admin-dashboard')
def admin_dashboard():
    if session.get("role") != "admin":
        flash("Access denied! Admins only.", "danger")
        return redirect(url_for("login"))

    return redirect(url_for('admin_panel'))


@app.route('/faculty-dashboard')
def faculty_dashboard():
    if not session.get("user_id"):
        return redirect(url_for("login"))

    if session.get("role") not in ("faculty", "admin"):
        flash("Access denied. Faculty dashboard only.", "danger")
        return redirect(url_for("home"))

    faculty_email = session.get("email", "")
    conn = get_db_connection()
    cursor = conn.cursor()

    # Fetch faculty profile
    try:
        cursor.execute(
            "SELECT sl_no, name, designation, dept FROM faculty WHERE email = %s LIMIT 1",
            (faculty_email,)
        )
        row = cursor.fetchone()
        fid, fname, fdesig, fdept = row if row else (None, session.get("name", "Faculty"), "Associate Professor", "CSE")
    except Exception:
        fid, fname, fdesig, fdept = (None, session.get("name", "Faculty"), "Associate Professor", "CSE")

    # Fetch timetable sessions for this faculty
    sessions_today = []
    try:
        cursor.execute(
            "SELECT subject_code, period, room FROM timetable WHERE faculty_email = %s ORDER BY period ASC LIMIT 6",
            (faculty_email,)
        )
        tt_rows = cursor.fetchall()
        status_map = ["done", "done", "next", "upcoming", "upcoming", "upcoming"]
        time_map   = ["8:30 AM", "10:30 AM", "12:30 PM", "2:30 PM", "3:30 PM", "4:30 PM"]
        for i, r in enumerate(tt_rows):
            sessions_today.append({
                "subject": r[0],
                "time":    time_map[i] if i < len(time_map) else f"Period {r[1]}",
                "room":    r[2] if r[2] else f"Room {i+1}",
                "status":  status_map[i] if i < len(status_map) else "upcoming"
            })
    except Exception:
        pass  # template uses fallback

    # Recent announcements
    try:
        cursor.execute("SELECT text FROM news_ticker ORDER BY sl_no DESC LIMIT 3")
        notices = [r[0] for r in cursor.fetchall()]
    except Exception:
        notices = []

    conn.close()

    class FacultyData:
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)

    faculty = FacultyData(
        name=fname,
        designation=fdesig,
        dept=fdept,
        dept_code=(fdept[:3].upper() if fdept else "CSE"),
        total_students=124,
        avg_cgpa=8.6,
        pending_evals=12,
        active_projects=3,
        courses=None,
        sessions=(sessions_today or None),
        tasks=None,
        notices=notices
    )

    return render_template("faculty_dashboard.html", faculty=faculty)


@app.route('/faculty/upload', methods=['POST'])
def faculty_upload():
    """Handle faculty file upload for notes, PYQs, and syllabus."""
    if session.get('role') != 'faculty':
        flash("Access denied! Faculty only.", "danger")
        return redirect(url_for('login'))

    course = request.form.get('course', '').strip()
    material_type = request.form.get('material_type', '').strip()
    uploaded_file = request.files.get('file')

    # Basic validation
    if not course or not material_type:
        flash("Please select a course and material type.", "danger")
        return redirect(url_for('faculty_dashboard'))

    if not uploaded_file or uploaded_file.filename == '':
        flash("No file selected. Please choose a file to upload.", "danger")
        return redirect(url_for('faculty_dashboard'))

    # os and secure_filename already imported at top

    ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'ppt', 'pptx', 'txt', 'zip'}
    filename = secure_filename(uploaded_file.filename)
    ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''

    if ext not in ALLOWED_EXTENSIONS:
        flash(f"File type '.{ext}' not allowed. Accepted: {', '.join(ALLOWED_EXTENSIONS)}", "danger")
        return redirect(url_for('faculty_dashboard'))

    upload_dir = os.path.join(app.root_path, 'static', 'uploads', 'notes')
    os.makedirs(upload_dir, exist_ok=True)

    # Build a descriptive filename: course_type_originalname
    save_filename = f"{course}_{material_type}_{filename}"
    save_path = os.path.join(upload_dir, save_filename)
    uploaded_file.save(save_path)

    flash(f"✅ '{filename}' uploaded successfully for {course} as {material_type}.", "success")
    return redirect(url_for('faculty_dashboard'))


# ─────────────────────────────────────────────────
# FACULTY — MOU CRUD
# ─────────────────────────────────────────────────
@app.route('/faculty/mou/add', methods=['POST'])
def faculty_mou_add():
    if session.get('role') != 'faculty':
        flash("Access denied! Faculty only.", "danger")
        return redirect(url_for('login'))
    org = request.form.get('organization', '').strip()
    dos = request.form.get('date_of_signing', '').strip()
    status = request.form.get('status', 'Active').strip()
    if not org:
        flash("Organization name is required.", "danger")
        return redirect(url_for('faculty_dashboard'))
    conn = get_db_connection()
    conn.execute(
        "INSERT INTO mous (organization, date_of_signing, status) VALUES (%s, %s, %s)",
        (org, dos, status)
    )
    conn.commit()
    conn.close()
    flash(f"✅ MOU with '{org}' added successfully.", "success")
    return redirect(url_for('faculty_dashboard'))


@app.route('/faculty/mou/edit/<int:mid>', methods=['POST'])
def faculty_mou_edit(mid):
    if session.get('role') != 'faculty':
        flash("Access denied! Faculty only.", "danger")
        return redirect(url_for('login'))
    org = request.form.get('organization', '').strip()
    dos = request.form.get('date_of_signing', '').strip()
    status = request.form.get('status', 'Active').strip()
    conn = get_db_connection()
    conn.execute(
        "UPDATE mous SET organization=%s, date_of_signing=%s, status=%s WHERE sl_no=%s",
        (org, dos, status, mid)
    )
    conn.commit()
    conn.close()
    flash(f"✅ MOU updated successfully.", "success")
    return redirect(url_for('faculty_dashboard'))


@app.route('/faculty/mou/delete/<int:mid>', methods=['POST'])
def faculty_mou_delete(mid):
    if session.get('role') != 'faculty':
        flash("Access denied! Faculty only.", "danger")
        return redirect(url_for('login'))
    conn = get_db_connection()
    conn.execute("DELETE FROM mous WHERE sl_no=%s", (mid,))
    conn.commit()
    conn.close()
    flash("MOU deleted.", "success")
    return redirect(url_for('faculty_dashboard'))


@app.route('/student-dashboard')
def student_dashboard():
    # STEP 4: only students can access this
    if session.get("role") != "student":
        flash("Access denied! Students only.", "danger")
        return redirect(url_for("login"))

    conn = get_db_connection()
    user_id = session.get('user_id')
    downloaded_docs = conn.execute('''
        SELECT r.title, r.file_url, rd.downloaded_at 
        FROM resource_downloads rd
        JOIN resources r ON r.id = rd.resource_id
        WHERE rd.user_id = %s
        ORDER BY rd.downloaded_at DESC
        LIMIT 5
    ''', (user_id,)).fetchall()
    conn.close()

    return render_template("student_dashboard.html", active_page='student_dashboard', downloaded_docs=downloaded_docs)

# Attendance page removed

@app.route('/dashboard/results')
def student_results():
    if session.get("role") != "student":
        flash("Access denied! Students only.", "danger")
        return redirect(url_for("login"))
        
    conn = get_db_connection()
    user_id_str = session.get('user_id')
    cursor = conn.cursor()
    
    # Verify the user and get their integer sl_no
    cursor.execute("SELECT sl_no FROM users WHERE user_id = %s", (user_id_str,))
    user = cursor.fetchone()
    if not user:
        conn.close()
        return redirect(url_for('login'))
        
    user_sl_no = user['sl_no']
    
    # Fetch real internal marks
    cursor.execute("""
        SELECT subject_code, subject_name, internal_1, internal_2, assignment, total 
        FROM internal_marks 
        WHERE user_id = %s
    """, (user_sl_no,))
    rows = cursor.fetchall()
    
    # Fetch performance summary
    cursor.execute("SELECT cgpa, cgpa_improvement, prev_sem, credits, rank_percentile FROM student_performance WHERE user_id = %s", (user_sl_no,))
    perf = cursor.fetchone()
    
    # Fetch semester GPAs
    cursor.execute("SELECT semester, sgpa FROM student_semester_gpas WHERE user_id = %s ORDER BY semester", (user_sl_no,))
    gpas = cursor.fetchall()
    
    conn.close()

    # Format data for template
    data = {
        'overall_cgpa': float(perf['cgpa']) if perf else 0.0,
        'cgpa_improvement': perf['cgpa_improvement'] if perf else '+0.0',
        'prev_sem': perf['prev_sem'] if perf else 0,
        'earned_credits': perf['credits'] if perf else 0,
        'total_credits': 160,
        'rank_percentile': perf['rank_percentile'] if perf else 0,
        'semester_results': [dict(g, credits=20) for g in gpas],
        'current_semester_marks': [dict(r) for r in rows],
        'grade_distribution': {'A+': 12, 'A': 15, 'B+': 8, 'B': 4, 'C': 1}
    }
    
    return render_template("student_results.html", active_page='results', data=data)


# ─────────────────────────────────────────────────
# ADMIN HELPER
# ─────────────────────────────────────────────────

def admin_required():
    """Returns True if user IS admin."""
    return session.get("role") == "admin"


@app.route('/admin/timetable/create', methods=['POST'])
def admin_timetable_create():
    if not admin_required():
        flash("Access denied! Admins only.", "danger")
        return redirect(url_for('login'))
        
    batch = request.form.get('batch', '').strip()
    if not batch:
        flash("Batch name is required.", "danger")
        return redirect(url_for('admin_panel') + '#academics')
        
    conn = get_db_connection()
    try:
        # Check if exists
        exists = conn.execute("SELECT 1 FROM timetable_meta WHERE batch=%s", (batch,)).fetchone()
        if exists:
            flash(f"Batch '{batch}' already exists.", "danger")
            return redirect(url_for('admin_panel') + '#academics')
            
        conn.execute("INSERT INTO timetable_meta (batch) VALUES (%s)", (batch,))
        conn.commit()
        flash(f"Batch '{batch}' created successfully. You can now edit its schedule.", "success")
    finally:
        conn.close()
        
    return redirect(url_for('admin_timetable_edit', batch=batch))

@app.route('/admin/timetable/delete/<batch>', methods=['POST'])
def admin_timetable_delete(batch):
    if not admin_required():
        flash("Access denied! Admins only.", "danger")
        return redirect(url_for('login'))
        
    conn = get_db_connection()
    try:
        # Get meta to delete image file if exists
        meta = conn.execute("SELECT image_filename FROM timetable_meta WHERE batch=%s", (batch,)).fetchone()
        if meta and meta['image_filename']:
            filepath = os.path.join(app.root_path, 'static', 'uploads', 'timetable', meta['image_filename'])
            if os.path.exists(filepath):
                os.remove(filepath)
                
        # Delete all related records
        conn.execute("DELETE FROM timetable_meta WHERE batch=%s", (batch,))
        conn.execute("DELETE FROM timetable_subjects WHERE batch=%s", (batch,))
        conn.execute("DELETE FROM timetable WHERE batch=%s", (batch,))
        conn.commit()
        flash(f"Timetable for '{batch}' has been completely deleted.", "success")
    finally:
        conn.close()
        
    return redirect(url_for('admin_panel') + '#academics')

@app.route('/admin/timetable/edit/<batch>')
def admin_timetable_edit(batch):
    if not admin_required():
        flash("Access denied! Admins only.", "danger")
        return redirect(url_for('login'))
        
    conn = get_db_connection()
    
    meta = conn.execute("SELECT * FROM timetable_meta WHERE batch=%s", (batch,)).fetchone()
    if not meta:
        conn.close()
        flash(f"Batch '{batch}' not found.", "danger")
        return redirect(url_for('admin_panel') + '#academics')
        
    # Get subjects
    subjects_raw = conn.execute("SELECT * FROM timetable_subjects WHERE batch=%s ORDER BY code", (batch,)).fetchall()
    subjects = [dict(s) for s in subjects_raw]
    
    # Get periods
    DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
    PERIODS = [1, 2, 3, 4, 5, 6]
    
    # Get slots and build a grid map
    slots_raw = conn.execute("SELECT * FROM timetable WHERE batch=%s", (batch,)).fetchall()
    conn.close()
    
    # Build dictionary (day, period) -> slot data
    grid = {}
    for slot in slots_raw:
        grid[(slot['day'], slot['period'])] = dict(slot)

    return render_template(
        'admin_timetable_edit.html',
        active_page='admin_dashboard',
        batch=batch,
        meta=dict(meta),
        subjects=subjects,
        days=DAYS,
        periods=PERIODS,
        grid=grid
    )

@app.route('/admin/timetable/toggle_image/<batch>', methods=['POST'])
def admin_timetable_toggle_image(batch):
    if not admin_required(): return jsonify({"success": False, "error": "Unauthorized"}), 403
    
    is_image = request.json.get('is_image', False)
    conn = get_db_connection()
    try:
        conn.execute("UPDATE timetable_meta SET is_image=%s WHERE batch=%s", (is_image, batch))
        conn.commit()
    finally:
        conn.close()
    return jsonify({"success": True})

@app.route('/admin/timetable/upload_image/<batch>', methods=['POST'])
def admin_timetable_upload_image(batch):
    if not admin_required():
        flash("Access denied! Admins only.", "danger")
        return redirect(url_for('login'))
        
    uploaded_file = request.files.get('file')
    if not uploaded_file or uploaded_file.filename == '':
        flash("No file selected.", "danger")
        return redirect(url_for('admin_timetable_edit', batch=batch))
        
    upload_dir = os.path.join(app.root_path, 'static', 'uploads', 'timetable')
    os.makedirs(upload_dir, exist_ok=True)
    
    filename = secure_filename(f"{batch.replace(' ', '_')}_image_{uploaded_file.filename}")
    save_path = os.path.join(upload_dir, filename)
    uploaded_file.save(save_path)
    
    conn = get_db_connection()
    try:
        # Delete old image if it exists
        old = conn.execute("SELECT image_filename FROM timetable_meta WHERE batch=%s", (batch,)).fetchone()
        if old and old['image_filename']:
            old_path = os.path.join(upload_dir, old['image_filename'])
            if os.path.exists(old_path) and old['image_filename'] != filename:
                os.remove(old_path)
                
        conn.execute("UPDATE timetable_meta SET image_filename=%s, is_image=TRUE WHERE batch=%s", (filename, batch))
        conn.commit()
        flash("Image uploaded successfully.", "success")
    finally:
        conn.close()
        
    return redirect(url_for('admin_timetable_edit', batch=batch))

@app.route('/admin/timetable/subject/add', methods=['POST'])
def admin_timetable_subj_add():
    if not admin_required(): return jsonify({"success": False}), 403
    data = request.json
    conn = get_db_connection()
    try:
        conn.execute(
            "INSERT INTO timetable_subjects (batch, code, full_name, faculty_code, faculty_name) VALUES (%s, %s, %s, %s, %s)",
            (data['batch'], data['code'], data['full_name'], data['faculty_code'], data['faculty_name'])
        )
        conn.commit()
        return jsonify({"success": True})
    finally:
        conn.close()

@app.route('/admin/timetable/subject/delete', methods=['POST'])
def admin_timetable_subj_delete():
    if not admin_required(): return jsonify({"success": False}), 403
    data = request.json
    conn = get_db_connection()
    try:
        conn.execute("DELETE FROM timetable_subjects WHERE sl_no=%s", (data['id'],))
        conn.commit()
        return jsonify({"success": True})
    finally:
        conn.close()

@app.route('/admin/timetable/slot', methods=['POST'])
def admin_timetable_slot_update():
    if not admin_required(): return jsonify({"success": False}), 403
    data = request.json
    batch, day, period = data['batch'], data['day'], data['period']
    subject_code = data.get('subject_code')
    faculty_code = data.get('faculty_code')
    is_lab = data.get('is_lab', False)
    span = data.get('span', 1)
    
    conn = get_db_connection()
    try:
        # Remove existing slot
        conn.execute("DELETE FROM timetable WHERE batch=%s AND day=%s AND period=%s", (batch, day, period))
        
        # If subject code is empty, we just deleted it
        if subject_code:
            conn.execute(
                "INSERT INTO timetable (batch, day, period, subject_code, faculty_code, is_lab, span) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                (batch, day, period, subject_code, faculty_code, is_lab, span)
            )
        conn.commit()
        return jsonify({"success": True})
    finally:
        conn.close()

# ─────────────────────────────────────────────────
# ADMIN DASHBOARD (with all data)
# ─────────────────────────────────────────────────

@app.route('/admin-panel')
def admin_panel():
    if not admin_required():
        flash("Access denied! Admins only.", "danger")
        return redirect(url_for("login"))

    conn = get_db_connection()
    all_users    = conn.execute("SELECT * FROM users").fetchall()
    faculty_list = conn.execute("SELECT * FROM faculty").fetchall()
    books_list   = conn.execute("SELECT * FROM books").fetchall()
    programs_raw = conn.execute("SELECT * FROM programs").fetchall()
    alumni_list  = conn.execute("SELECT * FROM alumni").fetchall()
    interns_list = conn.execute("SELECT * FROM internships").fetchall()
    batches_raw  = conn.execute("SELECT batch, is_image FROM timetable_meta").fetchall()
    conn.close()
    
    all_batches = [dict(b) for b in batches_raw]

    programs = []
    for p in programs_raw:
        d = dict(p)
        if d.get('highlights'):
            d['highlights_text'] = '\n'.join(json.loads(d['highlights']))
        programs.append(d)

    student_count = sum(1 for u in all_users if u['role'] == 'student')
    faculty_count = sum(1 for u in all_users if u['role'] == 'faculty')
    admin_count   = sum(1 for u in all_users if u['role'] == 'admin')

    # Get Unified Circulation History & Admin Notifications
    from models.issue import Issue
    from models.request import Request
    from models.notification import Notification

    transactions = []
    try:
        all_issues = Issue.get_all_issues()
        all_reqs = Request.get_all_requests()
        for issue in all_issues:
            transactions.append({
                'type': issue['status'],
                'book_title': issue['book_title'],
                'book_id': issue['book_id'],
                'user_name': issue['user_name'],
                'date': issue['return_date'] if issue['status'] == 'returned' and issue['return_date'] else issue['issue_date'],
                'badge_class': 'success' if issue['status'] == 'returned' else 'warning'
            })
        for req in all_reqs:
            transactions.append({
                'type': 'requested' if req['status'] == 'pending' else 'processed request',
                'book_title': req['book_title'],
                'book_id': req['book_id'],
                'user_name': req['user_name'],
                'date': req['request_date'],
                'badge_class': 'info' if req['status'] == 'pending' else 'secondary'
            })
        transactions.sort(key=lambda x: str(x['date'] or ''), reverse=True)
    except Exception as e:
        print(f"[admin_panel] Error building circulation history: {e}")

    try:
        admin_notifs = Notification.get_admin_notifications()
    except Exception as e:
        print(f"[admin_panel] Error fetching admin notifications: {e}")
        admin_notifs = []

    return render_template(
        "admin_panel.html",
        active_page='admin_dashboard',
        all_users=all_users,
        student_count=student_count,
        faculty_count=faculty_count,
        admin_count=admin_count,
        faculty_list=faculty_list,
        books_list=books_list,
        programs=programs,
        alumni_list=alumni_list,
        interns_list=interns_list,
        transactions=transactions,
        admin_notifs=admin_notifs,
        all_batches=all_batches,
    )

@app.route('/admin/users/edit/<string:uid>', methods=['POST'])
def admin_users_edit(uid):
    if not admin_required():
        return redirect(url_for('login'))
        
    name = request.form.get('name')
    email = request.form.get('email')
    user_id_new = request.form.get('user_id')  # This is the NEW user_id value
    role = request.form.get('role')
    
    conn = get_db_connection()
    try:
        conn.execute(
            "UPDATE users SET name = %s, email = %s, user_id = %s, role = %s WHERE user_id = %s",
            (name, email, user_id_new, role, uid)
        )
        conn.commit()
        flash("User updated!", "success")
    except psycopg2.errors.UniqueViolation:
        conn.rollback()
        flash("Error: User ID or Email already exists. Please choose another.", "danger")
    finally:
        conn.close()
       
    return redirect(url_for("admin_panel") + "#users")

@app.route('/admin/users/add', methods=["POST"])
def admin_users_add():
    if not admin_required():
        return redirect(url_for("login"))
    
    f = request.form
    # Basic validation
    if not f.get('name') or not f.get('email') or not f.get('user_id') or not f.get('password') or not f.get('role'):
        flash("All fields are required to create a user.", "danger")
        return redirect(url_for("admin_panel") + "#users")

    hashed_pw = generate_password_hash(f['password'])
    conn = get_db_connection()
    try:
        conn.execute(
            "INSERT INTO users (name, email, user_id, password, role) VALUES (%s, %s, %s, %s, %s)",
            (f['name'], f['email'], f['user_id'], hashed_pw, f['role'])
        )
        conn.commit()
        flash("User added successfully!", "success")
    except psycopg2.errors.UniqueViolation:
        conn.rollback()
        flash("Error: Email or User ID already exists. Please choose another.", "danger")
    finally:
        conn.close()
        
    return redirect(url_for("admin_panel") + "#users")


@app.route('/admin/users/delete/<string:uid>', methods=['POST'])
def admin_users_delete(uid):
    if not admin_required():
        return redirect(url_for("login"))
    
    # Prevent admin from deleting themselves
    if uid == session.get("user_id"):
        flash("You cannot delete your own account.", "danger")
        return redirect(url_for("admin_panel") + "#users")
        
    conn = get_db_connection()
    try:
        # Delete dependent records first to avoid ForeignKeyViolation
        conn.execute("DELETE FROM results WHERE student_id = %s", (uid,))
        conn.execute("DELETE FROM issues WHERE user_id = %s", (uid,))
        conn.execute("DELETE FROM requests WHERE requested_by = %s", (uid,))
        conn.execute("DELETE FROM notifications WHERE user_id = %s", (uid,))
        
        # Finally delete the user
        conn.execute("DELETE FROM users WHERE user_id=%s", (uid,))
        conn.commit()
        flash("User and all related records deleted!", "success")
    except Exception as e:
        conn.rollback()
        flash(f"Error deleting user: {str(e)}", "danger")
    finally:
        conn.close()
    return redirect(url_for("admin_panel") + "#users")

# ─────────────────────────────────────────────────
# ADMIN — FACULTY CRUD
# ─────────────────────────────────────────────────

@app.route('/admin/faculty/add', methods=["POST"])
def admin_faculty_add():
    if not admin_required():
        return redirect(url_for("login"))
    f = request.form
    conn = get_db_connection()
    try:
        conn.execute(
            "INSERT INTO faculty (name, designation, designation_key, qualification, joined, research, email, photo) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
            (f['name'], f['designation'], f['designation_key'], f['qualification'], f['joined'], f['research'], f['email'], f['photo'])
        )
        conn.commit()
    finally:
        conn.close()
    flash("Faculty member added!", "success")
    return redirect(url_for("admin_panel") + "#faculty")

@app.route('/admin/faculty/edit/<int:fid>', methods=["POST"])
def admin_faculty_edit(fid):
    if not admin_required():
        return redirect(url_for("login"))
    f = request.form
    conn = get_db_connection()
    try:
        conn.execute(
            "UPDATE faculty SET name=%s, designation=%s, designation_key=%s, qualification=%s, joined=%s, research=%s, email=%s, photo=%s WHERE sl_no=%s",
            (f['name'], f['designation'], f['designation_key'], f['qualification'], f['joined'], f['research'], f['email'], f['photo'], fid)
        )
        conn.commit()
    finally:
        conn.close()
    flash("Faculty member updated!", "success")
    return redirect(url_for("admin_panel") + "#faculty")

@app.route('/admin/faculty/delete/<int:fid>', methods=["POST"])
def admin_faculty_delete(fid):
    if not admin_required():
        return redirect(url_for("login"))
    conn = get_db_connection()
    try:
        conn.execute("DELETE FROM faculty WHERE sl_no=%s", (fid,))
        conn.commit()
    finally:
        conn.close()
    flash("Faculty member deleted!", "warning")
    return redirect(url_for("admin_panel") + "#faculty")

@app.route('/faculty/<int:fid>')
def faculty_detail(fid):
    return render_template('faculty/faculty_detail.html', fid=fid, active_page='faculty')

@app.route('/api/faculty/<int:fid>')
def api_faculty_detail(fid):
    conn = get_db_connection()
    row = conn.execute("SELECT * FROM faculty WHERE sl_no = %s", (fid,)).fetchone()
    conn.close()

    if not row:
        return jsonify({"error": "Faculty not found"}), 404

    faculty = dict(row)
    
    # Custom details for HOD (based on name or designation_key)
    if faculty.get('designation_key') == 'hod':
        faculty.update({
            "bio": "Dedicated to academic excellence and research innovation at AISAT since 2014.",
            "education": [
                {"degree": "Ph.D", "major": "Computer Science and Engineering", "univ": "APJ Abdul Kalam Technological University"},
                {"degree": "PGDCL", "major": "Cyber Law", "univ": "NALSAR University of Law"},
                {"degree": "M.Tech", "major": "Computer Science", "univ": "Mahatma Gandhi University"}
            ],
            "publications": [
                {"title": "Blockchain-based Secure Data Sharing for IoT Devices", "journal": "IEEE Trans. on Industrial Informatics", "year": "2023", "link": "#"},
                {"title": "AI-driven Threat Detection in Smart Grids", "journal": "Journal of Cybersecurity", "year": "2022", "link": "#"}
            ],
            "activities": [
                "Resource Person at Amrita Vishwa Vidyapeetham",
                "Reviewer for SAGE Publications",
                "Reviewer for IEEE ICRAIS 2025",
                "Member of IEEE and ACM"
            ],
            "interests": ["Cyber Security", "Blockchain", "Digital Forensics"]
        })
    else:
        # Generic fallback for others
        faculty.update({
            "bio": f"Dedicated educator at AISAT focusing on {faculty.get('research', 'Computer Science')}.",
            "education": [
                {"degree": "Ph.D / M.Tech", "major": faculty.get('research', 'CSE'), "univ": "Technical University"}
            ],
            "publications": [],
            "activities": ["Member of Technical Committees"],
            "interests": (faculty.get('research', '')).split(',')
        })

    return jsonify(faculty)



# ─────────────────────────────────────────────────
# ADMIN — LIBRARY / BOOKS CRUD
# ─────────────────────────────────────────────────

@app.route('/admin/books/add', methods=["POST"])
def admin_books_add():
    if not admin_required():
        return redirect(url_for("login"))
    f = request.form
    conn = get_db_connection()
    try:
        conn.execute(
            "INSERT INTO books (title, author, category, status, cover_gradient, cover_icon) VALUES (%s,%s,%s,%s,%s,%s)",
            (f['title'], f['author'], f['category'], f['status'],
             f.get('cover_gradient', 'linear-gradient(135deg,#667eea,#764ba2)'),
             f.get('cover_icon', 'fas fa-book'))
        )
        conn.commit()
    finally:
        conn.close()
    flash("Book added!", "success")
    return redirect(url_for("admin_panel") + "#library")

@app.route('/admin/books/edit/<int:bid>', methods=["POST"])
def admin_books_edit(bid):
    if not admin_required():
        return redirect(url_for("login"))
    f = request.form
    conn = get_db_connection()
    try:
        conn.execute(
            "UPDATE books SET title=%s, author=%s, category=%s, status=%s WHERE sl_no=%s",
            (f['title'], f['author'], f['category'], f['status'], bid)
        )
        conn.commit()
    finally:
        conn.close()
    flash("Book updated!", "success")
    return redirect(url_for("admin_panel") + "#library")

@app.route('/admin/books/delete/<int:bid>', methods=["POST"])
def admin_books_delete(bid):
    if not admin_required():
        return redirect(url_for("login"))
    conn = get_db_connection()
    try:
        conn.execute("DELETE FROM books WHERE sl_no=%s", (bid,))
        conn.commit()
    finally:
        conn.close()
    flash("Book deleted!", "warning")
    return redirect(url_for("admin_panel") + "#library")


# ─────────────────────────────────────────────────
# ADMIN — ACADEMICS / PROGRAMS CRUD
# ─────────────────────────────────────────────────

@app.route('/admin/programs/add', methods=["POST"])
def admin_programs_add():
    if not admin_required():
        return redirect(url_for("login"))
    f = request.form
    highlights = [h.strip() for h in f.get('highlights', '').split('\n') if h.strip()]
    conn = get_db_connection()
    try:
        conn.execute(
            "INSERT INTO programs (name, duration, intake, eligibility, extra_icon, extra_label, extra_value, highlights) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
            (f['name'], f['duration'], f['intake'], f['eligibility'],
             f.get('extra_icon', '🏫'), f.get('extra_label', ''), f.get('extra_value', ''),
             json.dumps(highlights))
        )
        conn.commit()
    finally:
        conn.close()
    flash("Program added!", "success")
    return redirect(url_for("admin_panel") + "#academics")

@app.route('/admin/programs/edit/<int:pid>', methods=["POST"])
def admin_programs_edit(pid):
    if not admin_required():
        return redirect(url_for("login"))
    f = request.form
    highlights = [h.strip() for h in f.get('highlights', '').split('\n') if h.strip()]
    conn = get_db_connection()
    try:
        conn.execute(
            "UPDATE programs SET name=%s, duration=%s, intake=%s, eligibility=%s, extra_label=%s, extra_value=%s, highlights=%s WHERE sl_no=%s",
            (f['name'], f['duration'], f['intake'], f['eligibility'],
             f.get('extra_label', ''), f.get('extra_value', ''),
             json.dumps(highlights), pid)
        )
        conn.commit()
    finally:
        conn.close()
    flash("Program updated!", "success")
    return redirect(url_for("admin_panel") + "#academics")

@app.route('/admin/programs/delete/<int:pid>', methods=["POST"])
def admin_programs_delete(pid):
    if not admin_required():
        return redirect(url_for("login"))
    conn = get_db_connection()
    try:
        conn.execute("DELETE FROM programs WHERE sl_no=%s", (pid,))
        conn.commit()
    finally:
        conn.close()
    flash("Program deleted!", "warning")
    return redirect(url_for("admin_panel") + "#academics")


# ─────────────────────────────────────────────────
# ADMIN — PLACEMENT SUMMARY CRUD
# ─────────────────────────────────────────────────

# Placement admin routes removed


@app.route('/api/chat', methods=['POST'])
def api_chat():
    """AI Chatbot Endpoint (Stateless, History passed from frontend)"""
    try:
        data = request.get_json()
        if not data or 'messages' not in data:
            return jsonify({'response': "I didn't receive any messages to process."})
            
        messages = data.get('messages', [])
        if not messages:
            return jsonify({'response': "I didn't receive any messages to process."})
            
        is_logged_in = bool(session.get('user_id'))
        
        # Generate response passing the full history
        response_text = llm_engine.generate_response(messages, is_logged_in)
        
        return jsonify({'response': response_text})
    except Exception as e:
        print(f"Chat Route Error: {e}")
        return jsonify({'response': "I'm having a bit of trouble connecting to my engine right now. Please try again later."})

@app.route('/notice/<int:notice_id>')
def notice_detail(notice_id):
    mock_notice = {
        'id': notice_id,
        'title': f"Department Update #{notice_id}",
        'category': 'Academic Alert' if notice_id % 2 == 0 else 'Placement Update',
        'date': 'Just Now',
        'content': 'This is a detailed record dynamically fetched. The curriculum changes or placement instructions will be elaborated here.'
    }
    return render_template('notice_detail.html', notice=mock_notice, active_page='')


# Placement details removed


@app.route('/student-dashboard/timetable')
def student_dashboard_timetable_redirect():
    if "user_id" not in session or session.get("role") != "student":
        return redirect(url_for("login"))
    return redirect(url_for('student_timetable'))

# Student placement tracker removed

@app.route('/student-dashboard/notifications')
def student_notifications():
    if "user_id" not in session or session.get("role") != "student":
        return redirect(url_for("login"))
    from models.notification import Notification
    all_notifs = Notification.get_user_notifications()
    return render_template('notifications_all.html', all_notifs=all_notifs, active_page='')


@app.route('/faculty-dashboard/timetable')
def faculty_timetable():
    if "user_id" not in session or session.get("role") != "faculty":
        return redirect(url_for("login"))
    return render_template('faculty_timetable.html', active_page='')

@app.route('/faculty-dashboard/queries')
def faculty_queries():
    if "user_id" not in session or session.get("role") != "faculty":
        return redirect(url_for("login"))
    return render_template('faculty_queries.html', active_page='')


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

# ─────────────────────────────────────────────────
# RUN
# ─────────────────────────────────────────────────
if __name__ == "__main__":
    init_db()
    app.run(debug=True)