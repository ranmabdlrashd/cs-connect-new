"""
Seed script: insert 4 Lab Room timetables.
Idempotent — skips batches that already exist in timetable_meta.
"""
import os, psycopg2, psycopg2.extras
from dotenv import load_dotenv

load_dotenv()

def get_conn():
    db_url = (os.environ.get("NEON_DATABASE_URL")
              or os.environ.get("LOCAL_DATABASE_URL")
              or os.environ.get("DATABASE_URL"))
    return psycopg2.connect(db_url)


def seed_batch(cur, batch, subjects, entries):
    """Insert meta + subjects + timetable rows for one batch."""
    cur.execute("SELECT 1 FROM timetable_meta WHERE batch=%s", (batch,))
    if cur.fetchone():
        print(f"  ⏭  {batch} already exists — skipping.")
        return

    cur.execute(
        "INSERT INTO timetable_meta (batch, is_image, image_filename) VALUES (%s, %s, %s)",
        (batch, False, None),
    )

    if subjects:
        cur.executemany(
            "INSERT INTO timetable_subjects (batch, code, full_name, faculty_code, faculty_name) "
            "VALUES (%s,%s,%s,%s,%s)",
            subjects,
        )

    cur.executemany(
        "INSERT INTO timetable (batch, day, period, subject_code, faculty_code, is_lab, span) "
        "VALUES (%s,%s,%s,%s,%s,%s,%s)",
        entries,
    )
    print(f"  ✅ {batch} seeded ({len(subjects)} subjects, {len(entries)} slots)")


# ═══════════════════════════════════════════════════
#  Lab A402 (S2,S8,S4)  — N/W Lab, Project, BCT, DM
# ═══════════════════════════════════════════════════
LAB_A402_S2S8S4_SUBJECTS = [
    ('Lab A402 (S2,S8,S4)', 'N/W LAB',  'Networking Lab',              'THV',     'Prof. A Thilakavathi'),
    ('Lab A402 (S2,S8,S4)', 'OS LAB',   'Operating Systems Lab',       'SHC',     'Prof. Shruthi Chandran'),
    ('Lab A402 (S2,S8,S4)', 'BCT',      'Blockchain Technologies',     'JRD',     'Dr. Jeswin Roy DCouth'),
    ('Lab A402 (S2,S8,S4)', 'DM',       'Data Mining',                 'DIM',     'Prof. Divya Mohan'),
    ('Lab A402 (S2,S8,S4)', 'PROJECT',  'Project Phase II',            'DIM,JRD', 'Prof. Divya Mohan, Dr. Jeswin Roy DCouth'),
    ('Lab A402 (S2,S8,S4)', 'P&T',      'Placement & Training',        '',        ''),
]

LAB_A402_S2S8S4_ENTRIES = [
    # MONDAY
    ('Lab A402 (S2,S8,S4)','Monday',2,'N/W LAB','THV',True,2),
    ('Lab A402 (S2,S8,S4)','Monday',5,'OS LAB [S4 CSE B]','SHC',True,2),
    # TUESDAY
    ('Lab A402 (S2,S8,S4)','Tuesday',1,'BCT','JRD',True,1),
    ('Lab A402 (S2,S8,S4)','Tuesday',2,'DM','DIM',True,1),
    ('Lab A402 (S2,S8,S4)','Tuesday',5,'N/W LAB','AIJ',True,2),
    # WEDNESDAY
    ('Lab A402 (S2,S8,S4)','Wednesday',2,'PROJECT','DIM',True,1),
    ('Lab A402 (S2,S8,S4)','Wednesday',5,'N/W LAB','SPM',True,2),
    # THURSDAY
    ('Lab A402 (S2,S8,S4)','Thursday',2,'N/W LAB','THV',True,2),
    ('Lab A402 (S2,S8,S4)','Thursday',5,'P&T','',False,2),
    # FRIDAY
    ('Lab A402 (S2,S8,S4)','Friday',1,'DM','DIM',True,1),
    ('Lab A402 (S2,S8,S4)','Friday',3,'BCT','JRD',True,1),
    ('Lab A402 (S2,S8,S4)','Friday',5,'PROJECT','DIM',True,2),
    # SATURDAY
    ('Lab A402 (S2,S8,S4)','Saturday',3,'PROJECT','DIM/JRD',True,4),
]


# ═══════════════════════════════════════════════════
#  Lab A402 (S2)  — CP Lab, IT W/S for S2 batches
# ═══════════════════════════════════════════════════
LAB_A402_S2_SUBJECTS = [
    ('Lab A402 (S2)', 'CP LAB',             'Programming in C Lab',                     'AAC',      'Prof. AAC'),
    ('Lab A402 (S2)', 'CP LAB DIPLOMA AIML','CP Lab Diploma AIML',                      'AAC',      'Prof. AAC'),
    ('Lab A402 (S2)', 'CP LAB DIPLOMA CS',  'CP Lab Diploma CS',                        '',         ''),
    ('Lab A402 (S2)', 'IT W/S',             'IT Workshop',                              'TEJ',      'Prof. Teenu Jose'),
    ('Lab A402 (S2)', 'P&T',                'Placement & Training',                     '',         ''),
]

LAB_A402_S2_ENTRIES = [
    # MONDAY
    ('Lab A402 (S2)','Monday',2,'CP LAB DIPLOMA AIML','AAC',True,2),
    ('Lab A402 (S2)','Monday',4,'S8EEE','',True,1),
    ('Lab A402 (S2)','Monday',5,'CP LAB [S2 EEE]','ANH,TIV',True,2),
    # TUESDAY
    ('Lab A402 (S2)','Tuesday',1,'CP LAB [S2 AI]','AAC',True,1),
    ('Lab A402 (S2)','Tuesday',3,'CP LAB [S2 CSE A]','THV',True,1),
    ('Lab A402 (S2)','Tuesday',5,'IT W/S [S2 CSE B]','SWC',True,2),
    # WEDNESDAY
    ('Lab A402 (S2)','Wednesday',1,'IT W/S [S2 CSE B]','SJC',True,1),
    ('Lab A402 (S2)','Wednesday',3,'IT W/S [S2 EEE]','RAK',True,1),
    ('Lab A402 (S2)','Wednesday',5,'IT W/S [S2 EC]','',True,1),
    # THURSDAY
    ('Lab A402 (S2)','Thursday',2,'IT W/S [S2 CSE A]','TEJ',True,2),
    ('Lab A402 (S2)','Thursday',5,'P&T','',False,2),
    # FRIDAY
    ('Lab A402 (S2)','Friday',1,'IT W/S [S2 EEE]','RAK',True,1),
    ('Lab A402 (S2)','Friday',3,'IT W/S [S2 AI]','ANV',True,1),
    ('Lab A402 (S2)','Friday',5,'CP LAB DIPLOMA CS','',True,2),
]


# ═══════════════════════════════════════════════════
#  Lab A401 (S4,S2,S8) — OS Lab, CP Lab, Project
# ═══════════════════════════════════════════════════
LAB_A401_SUBJECTS = [
    ('Lab A401 (S4,S2,S8)', 'CP LAB',   'Programming in C Lab',     'SPM',      'Prof. Sharija P M'),
    ('Lab A401 (S4,S2,S8)', 'OS LAB',   'Operating Systems Lab',    'SHC',      'Prof. Shruthi Chandran'),
    ('Lab A401 (S4,S2,S8)', 'PROJECT',  'Project (Database Lab)',   'DIM,JRD',  'Prof. Divya Mohan, Dr. Jeswin Roy DCouth'),
]

LAB_A401_ENTRIES = [
    # MONDAY
    ('Lab A401 (S4,S2,S8)','Monday',3,'CP LAB [S2 CSE B]','SPM',True,1),
    ('Lab A401 (S4,S2,S8)','Monday',5,'PROJECT [DB LAB]','DIM,JRD',True,2),
    # TUESDAY
    ('Lab A401 (S4,S2,S8)','Tuesday',5,'OS LAB [S4 CSE B]','SHC',True,2),
    # WEDNESDAY
    ('Lab A401 (S4,S2,S8)','Wednesday',2,'CP LAB [S2 AI]','KAS',True,1),
    ('Lab A401 (S4,S2,S8)','Wednesday',5,'OS LAB [S4 CSE A]','NJP',True,2),
    # THURSDAY
    ('Lab A401 (S4,S2,S8)','Thursday',1,'OS LAB [S4 AI]','AAC',True,2),
    ('Lab A401 (S4,S2,S8)','Thursday',5,'OS LAB [S4 CSE A]','NF',True,2),
    # FRIDAY
    ('Lab A401 (S4,S2,S8)','Friday',1,'OS LAB [S4 AI]','AAC',True,2),
    ('Lab A401 (S4,S2,S8)','Friday',5,'CP LAB [S2 CSE A]','THV',True,2),
]


# ═══════════════════════════════════════════════════
#  Lab DB (S2,S4,S6) — DBMS Lab, Mini Project, IT W/S, CP Lab
# ═══════════════════════════════════════════════════
LAB_DB_SUBJECTS = [
    ('Lab DB (S2,S4,S6)', 'MINI PROJECT', 'Mini Project',             'ANG',      'Prof. Angel Mathai'),
    ('Lab DB (S2,S4,S6)', 'DBMS LAB',     'DBMS Lab',                 'SPJ',      'Prof. Sinijoy P J'),
    ('Lab DB (S2,S4,S6)', 'IT W/S',       'IT Workshop',              'ANV',      'Prof. ANV'),
    ('Lab DB (S2,S4,S6)', 'CP LAB',       'Programming in C Lab',     'SPM',      'Prof. Sharija P M'),
]

LAB_DB_ENTRIES = [
    # MONDAY
    ('Lab DB (S2,S4,S6)','Monday',1,'MINI PROJECT [S6 CSE A]','ANG',True,3),
    ('Lab DB (S2,S4,S6)','Monday',5,'DBMS LAB [S4 CSE B]','SPJ',True,2),
    # TUESDAY
    ('Lab DB (S2,S4,S6)','Tuesday',1,'IT W/S [S2 AI]','ANV',True,1),
    ('Lab DB (S2,S4,S6)','Tuesday',5,'DBMS LAB [S4 CSE B]','KCJ',True,2),
    # WEDNESDAY
    ('Lab DB (S2,S4,S6)','Wednesday',1,'CP LAB [S2 CSE B]','SPM',True,1),
    ('Lab DB (S2,S4,S6)','Wednesday',5,'DBMS LAB [S4 CSE B]','TEJ',True,2),
    # THURSDAY
    ('Lab DB (S2,S4,S6)','Thursday',5,'DBMS LAB [S4 CSE B]','SHC',True,2),
    # FRIDAY
    ('Lab DB (S2,S4,S6)','Friday',1,'CP LAB [S2 EEE]','ANH,TIV',True,1),
    ('Lab DB (S2,S4,S6)','Friday',3,'CP LAB [S2 CSE B]','SPM',True,1),
    ('Lab DB (S2,S4,S6)','Friday',5,'IT W/S [S2 CSE A]','TEJ',True,2),
]


# ═══════════════════════════════════════════════════
#                      MAIN
# ═══════════════════════════════════════════════════
def main():
    conn = get_conn()
    cur = conn.cursor()

    print("Seeding lab timetables …")
    seed_batch(cur, 'Lab A402 (S2,S8,S4)', LAB_A402_S2S8S4_SUBJECTS, LAB_A402_S2S8S4_ENTRIES)
    seed_batch(cur, 'Lab A402 (S2)',       LAB_A402_S2_SUBJECTS,      LAB_A402_S2_ENTRIES)
    seed_batch(cur, 'Lab A401 (S4,S2,S8)', LAB_A401_SUBJECTS,         LAB_A401_ENTRIES)
    seed_batch(cur, 'Lab DB (S2,S4,S6)',   LAB_DB_SUBJECTS,           LAB_DB_ENTRIES)

    conn.commit()
    cur.close()
    conn.close()
    print("Done!")


if __name__ == "__main__":
    main()
