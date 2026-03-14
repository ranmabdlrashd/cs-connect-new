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
app.secret_key = os.environ.get("SECRET_KEY", "csconnectsecret")

from routes.library_routes import library_bp
from routes.admin_routes import admin_bp
import llm_engine

app.register_blueprint(library_bp)
app.register_blueprint(admin_bp)

# PostgreSQL Connection details
class DBConnection:
    def __init__(self):
        db_url = os.environ.get("NEON_DATABASE_URL") or os.environ.get("LOCAL_DATABASE_URL") or os.environ.get("DATABASE_URL")
        
        if db_url:
            self.conn = psycopg2.connect(db_url)
        else:
            # Fallback for old local config if env vars are missing
            DB_HOST = os.environ.get("DB_HOST", "localhost")
            DB_NAME = os.environ.get("DB_NAME", "csconnect")
            DB_USER = os.environ.get("DB_USER", "postgres")
            DB_PASS = os.environ.get("DB_PASS", "1234")
            self.conn = psycopg2.connect(
                host=DB_HOST, dbname=DB_NAME, user=DB_USER, password=DB_PASS
            )
    
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
    row = conn.execute("SELECT text FROM news_ticker ORDER BY id DESC LIMIT 1").fetchone()
    conn.close()
    return row[0] if row else ""

def get_home_stats():
    conn = get_db_connection()
    rows = conn.execute("SELECT value, label FROM home_stats ORDER BY id ASC").fetchall()
    conn.close()
    return [{"value": r[0], "label": r[1]} for r in rows]

def get_placement_batches():
    conn = get_db_connection()
    rows = conn.execute("SELECT batch_key, label, stats, companies FROM placement_batches ORDER BY id ASC").fetchall()
    conn.close()
    batches = []
    for r in rows:
        stats = r[2] if not isinstance(r[2], str) else json.loads(r[2])
        companies = r[3] if not isinstance(r[3], str) else json.loads(r[3])
        batches.append({
            "key": r[0],
            "label": r[1],
            "stats": stats,
            "companies": companies
        })
    return batches



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


# ─────────────────────────────────────────────────
# DATABASE SETUP
# ─────────────────────────────────────────────────
def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. users
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            user_id TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            role TEXT DEFAULT 'student'
        )
    ''')
    
    # 2. faculty
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS faculty (
            id SERIAL PRIMARY KEY,
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
            id SERIAL PRIMARY KEY,
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
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS issues (
            id SERIAL PRIMARY KEY,
            book_id INTEGER,
            user_id INTEGER,
            issue_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            return_date TIMESTAMP,
            status TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS requests (
            id SERIAL PRIMARY KEY,
            book_id INTEGER,
            requested_by INTEGER,
            request_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS notifications (
            id SERIAL PRIMARY KEY,
            user_id INTEGER,
            message TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            read_status BOOLEAN DEFAULT FALSE
        )
    ''')
    
    # 4. placement_summary
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS placement_summary (
            id SERIAL PRIMARY KEY,
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
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            url TEXT,
            sector TEXT
        )
    ''')
    
    # 6. alumni
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS alumni (
            id SERIAL PRIMARY KEY,
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
            id SERIAL PRIMARY KEY,
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
            id SERIAL PRIMARY KEY,
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
            id SERIAL PRIMARY KEY,
            title TEXT NOT NULL,
            subjects TEXT
        )
    ''')
    
    # 10. news_ticker
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS news_ticker (
            id SERIAL PRIMARY KEY,
            text TEXT
        )
    ''')
    
    # 11. home_stats
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS home_stats (
            id SERIAL PRIMARY KEY,
            value TEXT,
            label TEXT
        )
    ''')
    
    # 12. placement_batches
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS placement_batches (
            id SERIAL PRIMARY KEY,
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
            id SERIAL PRIMARY KEY,
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
            id SERIAL PRIMARY KEY,
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

    # 17. mous (Memorandum of Understanding)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS mous (
            id SERIAL PRIMARY KEY,
            organization TEXT NOT NULL,
            date_of_signing TEXT,
            status TEXT DEFAULT 'Active'
        )
    ''')

    conn.commit()
    conn.close()



# ─────────────────────────────────────────────────
# PAGE ROUTES
# ─────────────────────────────────────────────────

@app.route('/')
def home():
    return render_template(
        'indexn.html',
        active_page='home',
        stats=get_home_stats(),
        feature_cards=get_site_data('home_feature_cards'),
        events=get_site_data('home_events'),
    )


@app.route('/timetable')
def timetable():
    if not session.get('user_id'):
        flash("Please log in to view the timetable.", "warning")
        return redirect(url_for('login'))

    conn = get_db_connection()
    
    # Fetch all batches for dropdown
    batches_raw = conn.execute("SELECT DISTINCT batch FROM timetable_meta").fetchall()
    all_batches = [b['batch'] for b in batches_raw] if batches_raw else ['S2 CSE A']
    
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
    mous_raw = conn.execute("SELECT * FROM mous ORDER BY id ASC").fetchall()
    conn.close()
    mous = [dict(m) for m in mous_raw]

    return render_template(
        'about/about-cse.html',
        active_page='about_cse',
        dept_stats=get_site_data('dept_stats_overview'),
        dept_glance=get_site_data('dept_stats_glance'),
        peos=get_site_data('peos'),
        psos=get_site_data('psos'),
        milestones=get_site_data('milestones'),
        mous=mous,
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
    conn = get_db_connection()
    programs_raw = conn.execute('SELECT * FROM programs').fetchall()
    semesters_raw = conn.execute('SELECT * FROM semesters').fetchall()
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
    )





@app.route('/placements')
def placements():
    conn = get_db_connection()
    
    # 1. Summary
    summary_raw = conn.execute('SELECT * FROM placement_summary').fetchall()
    placement_summary = []
    for s in summary_raw:
        d = dict(s)
        d['decimal'] = bool(d['decimal_bool'])
        placement_summary.append(d)
        
    # 2. Companies
    companies = [dict(row) for row in conn.execute('SELECT * FROM placement_companies').fetchall()]
    
    # 3. Alumni
    alumni = [dict(row) for row in conn.execute('SELECT * FROM alumni').fetchall()]
    
    # 4. Internships
    internships = [dict(row) for row in conn.execute('SELECT * FROM internships').fetchall()]
    
    # 5. Batches (Complex - needs restructuring or kept simple for now)
    # The batch data is nested, so let's mock the fetch to keep templates working
    # We will need a `placement_batches` table later or just parse a JSON
    # For now, let's just fetch the rest and hardcode PLACEMENT_BATCHES
    batches = get_placement_batches()

    conn.close()

    return render_template(
        'placement.html',
        active_page='placements',
        placement_summary=placement_summary,
        batches=batches,
        companies=companies,
        alumni=alumni,
        internships=internships,
        team=get_site_data('placement_team', {}),
    )


# ─────────────────────────────────────────────────
# API ENDPOINTS — JSON for AJAX / JS dynamic loading
# ─────────────────────────────────────────────────

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


@app.route('/api/placements')
def api_placements():
    """Return placement data as JSON."""
    conn = get_db_connection()
    summary_raw = conn.execute('SELECT * FROM placement_summary').fetchall()
    conn.close()
    
    placement_summary = []
    for s in summary_raw:
        d = dict(s)
        d['decimal'] = bool(d['decimal_bool'])
        placement_summary.append(d)
        
    return jsonify({
        "summary": placement_summary,
        "batches": get_placement_batches(),
    })


@app.route('/api/stats')
def api_stats():
    """Return homepage stats as JSON."""
    return jsonify(get_home_stats())


# ─────────────────────────────────────────────────
# AUTH ROUTES
# ─────────────────────────────────────────────────

@app.route('/register', methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = generate_password_hash(request.form["password"])
        user_id = request.form["user_id"]
        role = request.form.get("role", "student")

        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO users (name, email, user_id, password, role) VALUES (%s, %s, %s, %s, %s)",
                (name, email, user_id, password, role)
            )
            conn.commit()
            flash("Account Created Successfully!", "success")
        except psycopg2.IntegrityError:
            flash("Email or User ID already exists!", "danger")
        finally:
            conn.close()

        return redirect(url_for("login"))

    return render_template("register.html", active_page='')


@app.route('/login', methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()
        conn.close()

        if user and check_password_hash(user[4], password):
            session["user_id"] = user[0]
            session["name"]    = user[1]
            session["role"]    = user[5]   # ← STEP 1: save role in session
            flash("Login successful!", "success")

            # ← STEP 2: redirect based on role
            if session["role"] == "admin":
                return redirect(url_for("admin_dashboard"))
            elif session["role"] == "faculty":
                return redirect(url_for("faculty_dashboard"))
            else:
                return redirect(url_for("student_dashboard"))
        else:
            flash("Invalid email or password!", "danger")

    return render_template("login.html", active_page='')


@app.route('/logout')
def logout():
    session.clear()
    flash("Logged out successfully!", "success")
    return redirect(url_for("login"))


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
    # STEP 4: only faculty can access this
    if session.get("role") != "faculty":
        flash("Access denied! Faculty only.", "danger")
        return redirect(url_for("login"))

    # Fetch all batches for the timetable widget
    conn = get_db_connection()
    batches_raw = conn.execute("SELECT DISTINCT batch FROM timetable_meta ORDER BY batch").fetchall()
    all_batches = [b['batch'] for b in batches_raw] if batches_raw else []
    mous_raw = conn.execute("SELECT * FROM mous ORDER BY id ASC").fetchall()
    mous = [dict(m) for m in mous_raw]
    conn.close()

    return render_template("faculty_dashboard.html",
                           active_page='faculty_dashboard',
                           all_batches=all_batches,
                           mous=mous)


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
        "UPDATE mous SET organization=%s, date_of_signing=%s, status=%s WHERE id=%s",
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
    conn.execute("DELETE FROM mous WHERE id=%s", (mid,))
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

    # Fetch all batches for the timetable widget
    conn = get_db_connection()
    batches_raw = conn.execute("SELECT DISTINCT batch FROM timetable_meta ORDER BY batch").fetchall()
    all_batches = [b['batch'] for b in batches_raw] if batches_raw else []
    conn.close()

    return render_template("student_dashboard.html",
                           active_page='student_dashboard',
                           all_batches=all_batches)


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
        conn.execute("DELETE FROM timetable_subjects WHERE id=%s", (data['id'],))
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
    companies_list = conn.execute("SELECT * FROM placement_companies").fetchall()
    summary_list = conn.execute("SELECT * FROM placement_summary").fetchall()
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
    
    all_issues = Issue.get_all_issues()
    all_reqs = Request.get_all_requests()
    admin_notifs = Notification.get_admin_notifications()

    transactions = []
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
        companies_list=companies_list,
        summary_list=summary_list,
        transactions=transactions,
        admin_notifs=admin_notifs,
        all_batches=all_batches,
    )

@app.route('/admin/users/edit/<int:uid>', methods=["POST"])
def admin_users_edit(uid):
    if not admin_required():
        return redirect(url_for("login"))
    f = request.form
    conn = get_db_connection()
    conn.execute(
        "UPDATE users SET name=%s, email=%s, role=%s WHERE id=%s",
        (f['name'], f['email'], f['role'], uid)
    )
    conn.commit()
    conn.close()
    flash("User updated!", "success")
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


@app.route('/admin/users/delete/<int:uid>', methods=["POST"])
def admin_users_delete(uid):
    if not admin_required():
        return redirect(url_for("login"))
    
    # Prevent admin from deleting themselves
    if uid == session.get("user_id"):
        flash("You cannot delete your own account.", "danger")
        return redirect(url_for("admin_panel") + "#users")
        
    conn = get_db_connection()
    conn.execute("DELETE FROM users WHERE id=%s", (uid,))
    conn.commit()
    conn.close()
    flash("User deleted!", "success")
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
            "UPDATE faculty SET name=%s, designation=%s, designation_key=%s, qualification=%s, joined=%s, research=%s, email=%s, photo=%s WHERE id=%s",
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
        conn.execute("DELETE FROM faculty WHERE id=%s", (fid,))
        conn.commit()
    finally:
        conn.close()
    flash("Faculty member deleted!", "warning")
    return redirect(url_for("admin_panel") + "#faculty")


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
            "UPDATE books SET title=%s, author=%s, category=%s, status=%s WHERE id=%s",
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
        conn.execute("DELETE FROM books WHERE id=%s", (bid,))
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
            "UPDATE programs SET name=%s, duration=%s, intake=%s, eligibility=%s, extra_label=%s, extra_value=%s, highlights=%s WHERE id=%s",
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
        conn.execute("DELETE FROM programs WHERE id=%s", (pid,))
        conn.commit()
    finally:
        conn.close()
    flash("Program deleted!", "warning")
    return redirect(url_for("admin_panel") + "#academics")


# ─────────────────────────────────────────────────
# ADMIN — PLACEMENT SUMMARY CRUD
# ─────────────────────────────────────────────────

@app.route('/admin/placement-summary/edit/<int:sid>', methods=["POST"])
def admin_placement_summary_edit(sid):
    if not admin_required():
        return redirect(url_for("login"))
    f = request.form
    conn = get_db_connection()
    try:
        conn.execute(
            "UPDATE placement_summary SET icon=%s, value=%s, label=%s, company=%s WHERE id=%s",
            (f['icon'], f['value'], f['label'], f.get('company', ''), sid)
        )
        conn.commit()
    finally:
        conn.close()
    flash("Placement summary updated!", "success")
    return redirect(url_for("admin_panel") + "#placements")


# ─────────────────────────────────────────────────
# ADMIN — PLACEMENT COMPANIES CRUD
# ─────────────────────────────────────────────────

@app.route('/admin/companies/add', methods=["POST"])
def admin_companies_add():
    if not admin_required():
        return redirect(url_for("login"))
    f = request.form
    conn = get_db_connection()
    try:
        conn.execute("INSERT INTO placement_companies (name, url, sector) VALUES (%s,%s,%s)",
                     (f['name'], f.get('url', ''), f.get('sector', 'IT')))
        conn.commit()
    finally:
        conn.close()
    flash("Company added!", "success")
    return redirect(url_for("admin_panel") + "#placements")

@app.route('/admin/companies/delete/<int:cid>', methods=["POST"])
def admin_companies_delete(cid):
    if not admin_required():
        return redirect(url_for("login"))
    conn = get_db_connection()
    try:
        conn.execute("DELETE FROM placement_companies WHERE id=%s", (cid,))
        conn.commit()
    finally:
        conn.close()
    flash("Company deleted!", "warning")
    return redirect(url_for("admin_panel") + "#placements")


# ─────────────────────────────────────────────────
# ADMIN — ALUMNI CRUD
# ─────────────────────────────────────────────────

@app.route('/admin/alumni/add', methods=["POST"])
def admin_alumni_add():
    if not admin_required():
        return redirect(url_for("login"))
    f = request.form
    conn = get_db_connection()
    try:
        conn.execute("INSERT INTO alumni (name, batch, company, package, photo, testimonial) VALUES (%s,%s,%s,%s,%s,%s)",
                     (f['name'], f['batch'], f['company'], f['package'], f.get('photo', ''), f.get('testimonial', '')))
        conn.commit()
    finally:
        conn.close()
    flash("Alumni added!", "success")
    return redirect(url_for("admin_panel") + "#placements")

@app.route('/admin/alumni/delete/<int:aid>', methods=["POST"])
def admin_alumni_delete(aid):
    if not admin_required():
        return redirect(url_for("login"))
    conn = get_db_connection()
    try:
        conn.execute("DELETE FROM alumni WHERE id=%s", (aid,))
        conn.commit()
    finally:
        conn.close()
    flash("Alumni deleted!", "warning")
    return redirect(url_for("admin_panel") + "#placements")


# ─────────────────────────────────────────────────
# ADMIN — INTERNSHIPS CRUD
# ─────────────────────────────────────────────────

@app.route('/admin/internships/add', methods=["POST"])
def admin_internships_add():
    if not admin_required():
        return redirect(url_for("login"))
    f = request.form
    conn = get_db_connection()
    try:
        conn.execute("INSERT INTO internships (title, company, domain, location, description, link) VALUES (%s,%s,%s,%s,%s,%s)",
                     (f['title'], f['company'], f.get('domain', 'IT'), f.get('location', ''), f.get('description', ''), f.get('link', '#')))
        conn.commit()
    finally:
        conn.close()
    flash("Internship added!", "success")
    return redirect(url_for("admin_panel") + "#placements")

@app.route('/admin/internships/delete/<int:iid>', methods=["POST"])
def admin_internships_delete(iid):
    if not admin_required():
        return redirect(url_for("login"))
    conn = get_db_connection()
    try:
        conn.execute("DELETE FROM internships WHERE id=%s", (iid,))
        conn.commit()
    finally:
        conn.close()
    flash("Internship deleted!", "warning")
    return redirect(url_for("admin_panel") + "#placements")


@app.route('/chat', methods=['POST'])
def chat():
    """AI Chatbot Endpoint with Session History"""
    user_msg = request.json.get('message', '').strip()
    if not user_msg:
        return jsonify({'response': "I didn't catch that. Could you please say it again?"})

    # Initialize chat history in session if not present
    if 'chat_history' not in session:
        session['chat_history'] = []

    # Get recent history
    chat_history = session['chat_history']
    is_logged_in = bool(session.get('user_id'))
    
    try:
        # Generate response passing the history
        response_text = llm_engine.generate_response(user_msg, chat_history, is_logged_in)
        
        # Update history
        chat_history.append({"role": "user", "content": user_msg})
        chat_history.append({"role": "assistant", "content": response_text})
        
        # Limit history size to prevent session cookie overflow (max 10 messages)
        session['chat_history'] = chat_history[-10:]
        session.modified = True
        
        return jsonify({'response': response_text})
    except Exception as e:
        print(f"Chat Route Error: {e}")
        return jsonify({'response': "I'm having a bit of trouble thinking right now. Please try again later or visit the CSE office!"})

# ─────────────────────────────────────────────────
# RUN
# ─────────────────────────────────────────────────
if __name__ == "__main__":
    init_db()
    app.run(debug=True)