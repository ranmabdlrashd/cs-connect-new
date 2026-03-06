from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

# Import mock data (replace with DB queries later)
from data import (
    NEWS_TICKER,
    HOME_STATS, HOME_FEATURE_CARDS, HOME_EVENTS,
    STAFF_DATA,
    DEPT_STATS_OVERVIEW, DEPT_STATS_GLANCE, PEOS, PSOS, MILESTONES,
    ACCREDITATIONS, INFRASTRUCTURE,
    PLACEMENT_TEAM,
)

app = Flask(__name__)
app.secret_key = "csconnectsecret"

DATABASE = "csconnect.db"

# ─────────────────────────────────────────────────
# CONTEXT PROCESSOR — injects globals into every template
# ─────────────────────────────────────────────────
@app.context_processor
def inject_globals():
    return {
        "ticker_text": NEWS_TICKER,
        "active_page": "",   # overridden per route
    }


# ─────────────────────────────────────────────────
# DATABASE SETUP
# ─────────────────────────────────────────────────
def init_db():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            user_id TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            role TEXT DEFAULT 'student'
        )
    """)
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
        stats=HOME_STATS,
        feature_cards=HOME_FEATURE_CARDS,
        events=HOME_EVENTS,
    )


def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/faculty')
def faculty():
    conn = get_db_connection()
    faculty_list = [dict(row) for row in conn.execute('SELECT * FROM faculty').fetchall()]
    conn.close()
    
    return render_template(
        'faculty/faculty.html',
        active_page='faculty',
        faculty=faculty_list,
        staff_members=STAFF_DATA,
    )


@app.route('/about-cse')
def about_cse():
    return render_template(
        'about/about-cse.html',
        active_page='about_cse',
        dept_stats=DEPT_STATS_OVERVIEW,
        dept_glance=DEPT_STATS_GLANCE,
        peos=PEOS,
        psos=PSOS,
        milestones=MILESTONES,
    )


@app.route('/about-aisat')
def about_aisat():
    return render_template(
        'about/about-aisat.html',
        active_page='about_aisat',
        accreditations=ACCREDITATIONS,
        infrastructure=INFRASTRUCTURE,
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
    from data import PLACEMENT_BATCHES
    batches = PLACEMENT_BATCHES

    conn.close()

    return render_template(
        'placement.html',
        active_page='placements',
        placement_summary=placement_summary,
        batches=batches,
        companies=companies,
        alumni=alumni,
        internships=internships,
        team=PLACEMENT_TEAM,
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
        query += " AND LOWER(name) LIKE ?"
        params.append(f"%{search}%")
        
    if designation and designation != 'all':
        query += " AND designation_key = ?"
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
        query += " AND (LOWER(title) LIKE ? OR LOWER(author) LIKE ?)"
        params.extend([f"%{search}%", f"%{search}%"])
        
    if category and category != 'all':
        query += " AND category = ?"
        params.append(category)
        
    if status and status != 'all':
        query += " AND status = ?"
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
        
    from data import PLACEMENT_BATCHES
        
    return jsonify({
        "summary": placement_summary,
        "batches": PLACEMENT_BATCHES,
    })


@app.route('/api/stats')
def api_stats():
    """Return homepage stats as JSON."""
    return jsonify(HOME_STATS)


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

        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO users (name, email, user_id, password, role) VALUES (?, ?, ?, ?, ?)",
                (name, email, user_id, password, role)
            )
            conn.commit()
            flash("Account Created Successfully!", "success")
        except sqlite3.IntegrityError:
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

        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
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
        "INSERT INTO faculty (name, designation, designation_key, qualification, joined, research, email, photo) VALUES (?,?,?,?,?,?,?,?)",
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
        "UPDATE faculty SET name=?, designation=?, designation_key=?, qualification=?, joined=?, research=?, email=?, photo=? WHERE id=?",
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
    conn.execute("DELETE FROM faculty WHERE id=?", (fid,))
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
        "INSERT INTO books (title, author, category, status, shelf, cover_gradient, cover_icon) VALUES (?,?,?,?,?,?,?)",
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
        "UPDATE books SET title=?, author=?, category=?, status=?, shelf=? WHERE id=?",
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
    conn.execute("DELETE FROM books WHERE id=?", (bid,))
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
        "INSERT INTO programs (name, duration, intake, eligibility, extra_icon, extra_label, extra_value, highlights) VALUES (?,?,?,?,?,?,?,?)",
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
        "UPDATE programs SET name=?, duration=?, intake=?, eligibility=?, extra_label=?, extra_value=?, highlights=? WHERE id=?",
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
    conn.execute("DELETE FROM programs WHERE id=?", (pid,))
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
        "UPDATE placement_summary SET icon=?, value=?, label=?, company=? WHERE id=?",
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
    conn.execute("INSERT INTO placement_companies (name, url, sector) VALUES (?,?,?)",
                 (f['name'], f.get('url', ''), f.get('sector', 'IT')))
    conn.commit(); conn.close()
    flash("Company added!", "success")
    return redirect(url_for("admin_panel") + "#placements")

@app.route('/admin/companies/delete/<int:cid>', methods=["POST"])
def admin_companies_delete(cid):
    if admin_required():
        return redirect(url_for("login"))
    conn = get_db_connection()
    conn.execute("DELETE FROM placement_companies WHERE id=?", (cid,))
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
    conn.execute("INSERT INTO alumni (name, batch, company, package, photo, testimonial) VALUES (?,?,?,?,?,?)",
                 (f['name'], f['batch'], f['company'], f['package'], f.get('photo', ''), f.get('testimonial', '')))
    conn.commit(); conn.close()
    flash("Alumni added!", "success")
    return redirect(url_for("admin_panel") + "#placements")

@app.route('/admin/alumni/delete/<int:aid>', methods=["POST"])
def admin_alumni_delete(aid):
    if admin_required():
        return redirect(url_for("login"))
    conn = get_db_connection()
    conn.execute("DELETE FROM alumni WHERE id=?", (aid,))
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
    conn.execute("INSERT INTO internships (title, company, domain, location, description, link) VALUES (?,?,?,?,?,?)",
                 (f['title'], f['company'], f.get('domain', 'IT'), f.get('location', ''), f.get('description', ''), f.get('link', '#')))
    conn.commit(); conn.close()
    flash("Internship added!", "success")
    return redirect(url_for("admin_panel") + "#placements")

@app.route('/admin/internships/delete/<int:iid>', methods=["POST"])
def admin_internships_delete(iid):
    if admin_required():
        return redirect(url_for("login"))
    conn = get_db_connection()
    conn.execute("DELETE FROM internships WHERE id=?", (iid,))
    conn.commit(); conn.close()
    flash("Internship deleted!", "warning")
    return redirect(url_for("admin_panel") + "#placements")


# ─────────────────────────────────────────────────
# RUN
# ─────────────────────────────────────────────────
if __name__ == "__main__":
    init_db()
    app.run(debug=True)