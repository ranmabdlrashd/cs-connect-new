from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
import psycopg2
import psycopg2.extras
from werkzeug.security import generate_password_hash, check_password_hash


app = Flask(__name__)
app.secret_key = "csconnectsecret"

import os
from dotenv import load_dotenv

load_dotenv()

# PostgreSQL Connection details
DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_NAME = os.environ.get("DB_NAME", "login")
DB_USER = os.environ.get("DB_USER", "postgres")
DB_PASS = os.environ.get("DB_PASS", "1234")

class DBConnection:
    def __init__(self):
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
        
    def close(self):
        self.conn.close()

def get_db_connection():
    return DBConnection()

import json

def get_site_data(key, default_val=None):
    conn = get_db_connection()
    row = conn.execute("SELECT data FROM site_data WHERE key = %s", (key,)).fetchone()
    conn.close()
    if row and row[0]:
        # Handle if it's already a string or a dict/list because of jsonb
        if isinstance(row[0], str):
            return json.loads(row[0])
        return row[0]
    return default_val if default_val is not None else []

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
    return {
        "ticker_text": get_news_ticker(),
        "active_page": "",   # overridden per route
    }


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
            shelf TEXT,
            cover_gradient TEXT,
            cover_icon TEXT
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
    return render_template(
        'about/about-cse.html',
        active_page='about_cse',
        dept_stats=get_site_data('dept_stats_overview'),
        dept_glance=get_site_data('dept_stats_glance'),
        peos=get_site_data('peos'),
        psos=get_site_data('psos'),
        milestones=get_site_data('milestones'),
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

    import json
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


@app.route('/library')
def library():
    conn = get_db_connection()
    books = [dict(row) for row in conn.execute('SELECT * FROM books').fetchall()]
    conn.close()

    return render_template(
        'library/library.html',
        active_page='library',
        books=books,
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

    conn = get_db_connection()
    all_users = conn.execute("SELECT * FROM users").fetchall()
    conn.close()

    student_count = sum(1 for u in all_users if u['role'] == 'student')
    faculty_count = sum(1 for u in all_users if u['role'] == 'faculty')
    admin_count   = sum(1 for u in all_users if u['role'] == 'admin')

    return render_template("admin_dashboard.html",
                           active_page='admin_dashboard',
                           all_users=all_users,
                           student_count=student_count,
                           faculty_count=faculty_count,
                           admin_count=admin_count)


@app.route('/faculty-dashboard')
def faculty_dashboard():
    # STEP 4: only faculty can access this
    if session.get("role") != "faculty":
        flash("Access denied! Faculty only.", "danger")
        return redirect(url_for("login"))

    return render_template("faculty_dashboard.html",
                           active_page='faculty_dashboard')


@app.route('/student-dashboard')
def student_dashboard():
    # STEP 4: only students can access this
    if session.get("role") != "student":
        flash("Access denied! Students only.", "danger")
        return redirect(url_for("login"))

    return render_template("student_dashboard.html",
                           active_page='student_dashboard')




# ─────────────────────────────────────────────────
# ADMIN HELPER
# ─────────────────────────────────────────────────

def admin_required():
    """Returns True if user is NOT admin (i.e. should be denied)."""
    return session.get("role") != "admin"


# ─────────────────────────────────────────────────
# ADMIN DASHBOARD (with all data)
# ─────────────────────────────────────────────────

@app.route('/admin-panel')
def admin_panel():
    if admin_required():
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
    conn.close()

    import json
    programs = []
    for p in programs_raw:
        d = dict(p)
        if d.get('highlights'):
            d['highlights_text'] = '\n'.join(json.loads(d['highlights']))
        programs.append(d)

    student_count = sum(1 for u in all_users if u['role'] == 'student')
    faculty_count = sum(1 for u in all_users if u['role'] == 'faculty')
    admin_count   = sum(1 for u in all_users if u['role'] == 'admin')

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
    )


# ─────────────────────────────────────────────────
# ADMIN — FACULTY CRUD
# ─────────────────────────────────────────────────

@app.route('/admin/faculty/add', methods=["POST"])
def admin_faculty_add():
    if admin_required():
        return redirect(url_for("login"))
    f = request.form
    conn = get_db_connection()
    conn.execute(
        "INSERT INTO faculty (name, designation, designation_key, qualification, joined, research, email, photo) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
        (f['name'], f['designation'], f['designation_key'], f['qualification'], f['joined'], f['research'], f['email'], f['photo'])
    )
    conn.commit(); conn.close()
    flash("Faculty member added!", "success")
    return redirect(url_for("admin_panel") + "#faculty")

@app.route('/admin/faculty/edit/<int:fid>', methods=["POST"])
def admin_faculty_edit(fid):
    if admin_required():
        return redirect(url_for("login"))
    f = request.form
    conn = get_db_connection()
    conn.execute(
        "UPDATE faculty SET name=%s, designation=%s, designation_key=%s, qualification=%s, joined=%s, research=%s, email=%s, photo=%s WHERE id=%s",
        (f['name'], f['designation'], f['designation_key'], f['qualification'], f['joined'], f['research'], f['email'], f['photo'], fid)
    )
    conn.commit(); conn.close()
    flash("Faculty member updated!", "success")
    return redirect(url_for("admin_panel") + "#faculty")

@app.route('/admin/faculty/delete/<int:fid>', methods=["POST"])
def admin_faculty_delete(fid):
    if admin_required():
        return redirect(url_for("login"))
    conn = get_db_connection()
    conn.execute("DELETE FROM faculty WHERE id=%s", (fid,))
    conn.commit(); conn.close()
    flash("Faculty member deleted!", "warning")
    return redirect(url_for("admin_panel") + "#faculty")


# ─────────────────────────────────────────────────
# ADMIN — LIBRARY / BOOKS CRUD
# ─────────────────────────────────────────────────

@app.route('/admin/books/add', methods=["POST"])
def admin_books_add():
    if admin_required():
        return redirect(url_for("login"))
    f = request.form
    conn = get_db_connection()
    conn.execute(
        "INSERT INTO books (title, author, category, status, shelf, cover_gradient, cover_icon) VALUES (%s,%s,%s,%s,%s,%s,%s)",
        (f['title'], f['author'], f['category'], f['status'], f['shelf'],
         f.get('cover_gradient', 'linear-gradient(135deg,#667eea,#764ba2)'),
         f.get('cover_icon', 'fas fa-book'))
    )
    conn.commit(); conn.close()
    flash("Book added!", "success")
    return redirect(url_for("admin_panel") + "#library")

@app.route('/admin/books/edit/<int:bid>', methods=["POST"])
def admin_books_edit(bid):
    if admin_required():
        return redirect(url_for("login"))
    f = request.form
    conn = get_db_connection()
    conn.execute(
        "UPDATE books SET title=%s, author=%s, category=%s, status=%s, shelf=%s WHERE id=%s",
        (f['title'], f['author'], f['category'], f['status'], f['shelf'], bid)
    )
    conn.commit(); conn.close()
    flash("Book updated!", "success")
    return redirect(url_for("admin_panel") + "#library")

@app.route('/admin/books/delete/<int:bid>', methods=["POST"])
def admin_books_delete(bid):
    if admin_required():
        return redirect(url_for("login"))
    conn = get_db_connection()
    conn.execute("DELETE FROM books WHERE id=%s", (bid,))
    conn.commit(); conn.close()
    flash("Book deleted!", "warning")
    return redirect(url_for("admin_panel") + "#library")


# ─────────────────────────────────────────────────
# ADMIN — ACADEMICS / PROGRAMS CRUD
# ─────────────────────────────────────────────────

@app.route('/admin/programs/add', methods=["POST"])
def admin_programs_add():
    if admin_required():
        return redirect(url_for("login"))
    import json
    f = request.form
    highlights = [h.strip() for h in f.get('highlights', '').split('\n') if h.strip()]
    conn = get_db_connection()
    conn.execute(
        "INSERT INTO programs (name, duration, intake, eligibility, extra_icon, extra_label, extra_value, highlights) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
        (f['name'], f['duration'], f['intake'], f['eligibility'],
         f.get('extra_icon', '🏫'), f.get('extra_label', ''), f.get('extra_value', ''),
         json.dumps(highlights))
    )
    conn.commit(); conn.close()
    flash("Program added!", "success")
    return redirect(url_for("admin_panel") + "#academics")

@app.route('/admin/programs/edit/<int:pid>', methods=["POST"])
def admin_programs_edit(pid):
    if admin_required():
        return redirect(url_for("login"))
    import json
    f = request.form
    highlights = [h.strip() for h in f.get('highlights', '').split('\n') if h.strip()]
    conn = get_db_connection()
    conn.execute(
        "UPDATE programs SET name=%s, duration=%s, intake=%s, eligibility=%s, extra_label=%s, extra_value=%s, highlights=%s WHERE id=%s",
        (f['name'], f['duration'], f['intake'], f['eligibility'],
         f.get('extra_label', ''), f.get('extra_value', ''),
         json.dumps(highlights), pid)
    )
    conn.commit(); conn.close()
    flash("Program updated!", "success")
    return redirect(url_for("admin_panel") + "#academics")

@app.route('/admin/programs/delete/<int:pid>', methods=["POST"])
def admin_programs_delete(pid):
    if admin_required():
        return redirect(url_for("login"))
    conn = get_db_connection()
    conn.execute("DELETE FROM programs WHERE id=%s", (pid,))
    conn.commit(); conn.close()
    flash("Program deleted!", "warning")
    return redirect(url_for("admin_panel") + "#academics")


# ─────────────────────────────────────────────────
# ADMIN — PLACEMENT SUMMARY CRUD
# ─────────────────────────────────────────────────

@app.route('/admin/placement-summary/edit/<int:sid>', methods=["POST"])
def admin_placement_summary_edit(sid):
    if admin_required():
        return redirect(url_for("login"))
    f = request.form
    conn = get_db_connection()
    conn.execute(
        "UPDATE placement_summary SET icon=%s, value=%s, label=%s, company=%s WHERE id=%s",
        (f['icon'], f['value'], f['label'], f.get('company', ''), sid)
    )
    conn.commit(); conn.close()
    flash("Placement summary updated!", "success")
    return redirect(url_for("admin_panel") + "#placements")


# ─────────────────────────────────────────────────
# ADMIN — PLACEMENT COMPANIES CRUD
# ─────────────────────────────────────────────────

@app.route('/admin/companies/add', methods=["POST"])
def admin_companies_add():
    if admin_required():
        return redirect(url_for("login"))
    f = request.form
    conn = get_db_connection()
    conn.execute("INSERT INTO placement_companies (name, url, sector) VALUES (%s,%s,%s)",
                 (f['name'], f.get('url', ''), f.get('sector', 'IT')))
    conn.commit(); conn.close()
    flash("Company added!", "success")
    return redirect(url_for("admin_panel") + "#placements")

@app.route('/admin/companies/delete/<int:cid>', methods=["POST"])
def admin_companies_delete(cid):
    if admin_required():
        return redirect(url_for("login"))
    conn = get_db_connection()
    conn.execute("DELETE FROM placement_companies WHERE id=%s", (cid,))
    conn.commit(); conn.close()
    flash("Company deleted!", "warning")
    return redirect(url_for("admin_panel") + "#placements")


# ─────────────────────────────────────────────────
# ADMIN — ALUMNI CRUD
# ─────────────────────────────────────────────────

@app.route('/admin/alumni/add', methods=["POST"])
def admin_alumni_add():
    if admin_required():
        return redirect(url_for("login"))
    f = request.form
    conn = get_db_connection()
    conn.execute("INSERT INTO alumni (name, batch, company, package, photo, testimonial) VALUES (%s,%s,%s,%s,%s,%s)",
                 (f['name'], f['batch'], f['company'], f['package'], f.get('photo', ''), f.get('testimonial', '')))
    conn.commit(); conn.close()
    flash("Alumni added!", "success")
    return redirect(url_for("admin_panel") + "#placements")

@app.route('/admin/alumni/delete/<int:aid>', methods=["POST"])
def admin_alumni_delete(aid):
    if admin_required():
        return redirect(url_for("login"))
    conn = get_db_connection()
    conn.execute("DELETE FROM alumni WHERE id=%s", (aid,))
    conn.commit(); conn.close()
    flash("Alumni deleted!", "warning")
    return redirect(url_for("admin_panel") + "#placements")


# ─────────────────────────────────────────────────
# ADMIN — INTERNSHIPS CRUD
# ─────────────────────────────────────────────────

@app.route('/admin/internships/add', methods=["POST"])
def admin_internships_add():
    if admin_required():
        return redirect(url_for("login"))
    f = request.form
    conn = get_db_connection()
    conn.execute("INSERT INTO internships (title, company, domain, location, description, link) VALUES (%s,%s,%s,%s,%s,%s)",
                 (f['title'], f['company'], f.get('domain', 'IT'), f.get('location', ''), f.get('description', ''), f.get('link', '#')))
    conn.commit(); conn.close()
    flash("Internship added!", "success")
    return redirect(url_for("admin_panel") + "#placements")

@app.route('/admin/internships/delete/<int:iid>', methods=["POST"])
def admin_internships_delete(iid):
    if admin_required():
        return redirect(url_for("login"))
    conn = get_db_connection()
    conn.execute("DELETE FROM internships WHERE id=%s", (iid,))
    conn.commit(); conn.close()
    flash("Internship deleted!", "warning")
    return redirect(url_for("admin_panel") + "#placements")


# ─────────────────────────────────────────────────
# RUN
# ─────────────────────────────────────────────────
if __name__ == "__main__":
    init_db()
    app.run(debug=True)