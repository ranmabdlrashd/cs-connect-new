"""
Seed script: insert S6 CSE B and S6 CSE A timetables.
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
#           S6 CSE B  (Room A409)
# ═══════════════════════════════════════════════════
S6_CSE_B_SUBJECTS = [
    ('S6 CSE B', 'CD',       'CST302 Compiler Design',                          'SPM',     'Prof. Sharija P M'),
    ('S6 CSE B', 'CG & IP',  'CST304 Computer Graphics & Image Processing',     'KCJ',     'Prof. Krishna C J'),
    ('S6 CSE B', 'AAD',      'CST306 Algorithm Analysis and Design',            'TEJ',     'Prof. Teenu Jose'),
    ('S6 CSE B', 'DA',       'CST322 Data Analytics',                           'JRD',     'Dr. Jeswin Roy DCouth'),
    ('S6 CSE B', 'IEF',      'HUT300 Industrial Economics & Foreign Trade',     'RPL',     'Prof. Rose Paul'),
    ('S6 CSE B', 'CCW',      'CST308 Comprehensive Course Work',                'AIJ',     'Prof. Anna Isabel John'),
    ('S6 CSE B', 'N/W LAB',  'CSL332 Networking Lab',                           'SPM,AIJ', 'Prof. Sharija P M, Prof. Anna Isabel John'),
    ('S6 CSE B', 'MINI PROJECT', 'CSD334 Miniproject',                          'NJP,AIJ', 'Prof. Nisy John Panicker, Prof. Anna Isabel John'),
    ('S6 CSE B', 'ACTIVITY', 'Activity Hour',                                    '',        ''),
]

S6_CSE_B_ENTRIES = [
    # MONDAY
    ('S6 CSE B','Monday',1,'CD','SPM',False,1),
    ('S6 CSE B','Monday',2,'IEF','RPL',False,1),
    ('S6 CSE B','Monday',3,'AAD','TEJ',False,1),
    ('S6 CSE B','Monday',4,'CCW','AIJ',False,1),
    ('S6 CSE B','Monday',5,'DA(R)','JRD',False,1),
    ('S6 CSE B','Monday',6,'CG','KRC',False,1),
    # TUESDAY
    ('S6 CSE B','Tuesday',1,'AAD','TEJ',False,1),
    ('S6 CSE B','Tuesday',2,'CD(R)','SPM',False,1),
    ('S6 CSE B','Tuesday',3,'DA(T)','JRD',False,1),
    ('S6 CSE B','Tuesday',5,'N/W LAB/MINI PROJECT','AIJ/NJP',True,2),
    # WEDNESDAY
    ('S6 CSE B','Wednesday',1,'AAD','TEJ',False,1),
    ('S6 CSE B','Wednesday',2,'IEF','RPL',False,1),
    ('S6 CSE B','Wednesday',3,'CG','KRC',False,1),
    ('S6 CSE B','Wednesday',5,'N/W LAB/MINI PROJECT','SPM/AIJ',True,2),
    # THURSDAY
    ('S6 CSE B','Thursday',1,'AAD(R)','TEJ',False,1),
    ('S6 CSE B','Thursday',2,'CD(T)','SPM',False,1),
    ('S6 CSE B','Thursday',3,'DA','JRD',False,1),
    ('S6 CSE B','Thursday',4,'CG(T)','KRC',False,1),
    ('S6 CSE B','Thursday',6,'P&T','',False,1),
    # FRIDAY
    ('S6 CSE B','Friday',1,'CG','KRC',False,1),
    ('S6 CSE B','Friday',2,'AAD(T)','TEJ',False,1),
    ('S6 CSE B','Friday',3,'IEF','RPL',False,1),
    ('S6 CSE B','Friday',4,'CG(R)','KRC',False,1),
    ('S6 CSE B','Friday',5,'CD','SPM',False,1),
    ('S6 CSE B','Friday',6,'CD','SPM',False,1),
    # SATURDAY
    ('S6 CSE B','Saturday',1,'CG','KRC',False,1),
    ('S6 CSE B','Saturday',2,'CCW','AIJ',False,1),
    ('S6 CSE B','Saturday',3,'CD','SPM',False,1),
    ('S6 CSE B','Saturday',4,'ACTIVITY','',False,1),
    ('S6 CSE B','Saturday',5,'AAD','TEJ',False,1),
    ('S6 CSE B','Saturday',6,'DA','JRD',False,1),
]


# ═══════════════════════════════════════════════════
#           S6 CSE A  (Room A408)
# ═══════════════════════════════════════════════════
S6_CSE_A_SUBJECTS = [
    ('S6 CSE A', 'CD',       'CST302 Compiler Design',                          'THV',     'Prof. A Thilakavathi'),
    ('S6 CSE A', 'CG & IP',  'CST304 Computer Graphics & Image Processing',     'SPJ',     'Prof. Sinijoy P J'),
    ('S6 CSE A', 'AAD',      'CST306 Algorithm Analysis and Design',            'NF',      'New Faculty 1'),
    ('S6 CSE A', 'DA',       'CST322 Data Analytics',                           'DIM',     'Prof. Divya Mohan'),
    ('S6 CSE A', 'IEF',      'HUT300 Industrial Economics & Foreign Trade',     'RPL',     'Prof. Rose Paul'),
    ('S6 CSE A', 'CCW',      'CST308 Comprehensive Course Work',                'AIJ',     'Prof. Anna Isabel John'),
    ('S6 CSE A', 'N/W LAB',  'CSL332 Networking Lab',                           'THV',     'Prof. A Thilakavathi'),
    ('S6 CSE A', 'MINI PROJECT', 'CSD334 Miniproject',                          'DIM,ANG', 'Prof. Divya Mohan, Prof. Angel Mathai'),
    ('S6 CSE A', 'ACTIVITY', 'Activity Hour',                                    '',        ''),
]

S6_CSE_A_ENTRIES = [
    # MONDAY
    ('S6 CSE A','Monday',1,'N/W LAB/MINI PROJECT','THV/ANG',True,3),
    ('S6 CSE A','Monday',4,'AAD','NF',False,1),
    ('S6 CSE A','Monday',5,'AAD(R)','NF',False,1),
    ('S6 CSE A','Monday',6,'CD(T)','THV',False,1),
    # TUESDAY
    ('S6 CSE A','Tuesday',1,'IEF','RPL',False,1),
    ('S6 CSE A','Tuesday',2,'CD','THV',False,1),
    ('S6 CSE A','Tuesday',3,'AAD(T)','NF',False,1),
    ('S6 CSE A','Tuesday',4,'DA(T)','DIM',False,1),
    ('S6 CSE A','Tuesday',5,'CG','SPJ',False,1),
    ('S6 CSE A','Tuesday',6,'CG(R)','SPJ',False,1),
    # WEDNESDAY
    ('S6 CSE A','Wednesday',1,'CD(R)','THV',False,1),
    ('S6 CSE A','Wednesday',2,'AAD','NF',False,1),
    ('S6 CSE A','Wednesday',3,'AAD','NF',False,1),
    ('S6 CSE A','Wednesday',4,'CD','THV',False,1),
    ('S6 CSE A','Wednesday',5,'IEF','RPL',False,1),
    ('S6 CSE A','Wednesday',6,'DA','DIM',False,1),
    # THURSDAY
    ('S6 CSE A','Thursday',1,'N/W LAB/MINI PROJECT','THV/DIM',True,3),
    ('S6 CSE A','Thursday',4,'CG','SPJ',False,1),
    ('S6 CSE A','Thursday',6,'P&T','',False,1),
    # FRIDAY
    ('S6 CSE A','Friday',1,'CG','SPJ',False,1),
    ('S6 CSE A','Friday',2,'CD','THV',False,1),
    ('S6 CSE A','Friday',3,'DA(R)','DIM',False,1),
    ('S6 CSE A','Friday',4,'CG(T)','SPJ',False,1),
    ('S6 CSE A','Friday',5,'CCW','AIJ',False,1),
    ('S6 CSE A','Friday',6,'IEF','RPL',False,1),
    # SATURDAY
    ('S6 CSE A','Saturday',1,'AAD','NF',False,1),
    ('S6 CSE A','Saturday',2,'DA','DIM',False,1),
    ('S6 CSE A','Saturday',3,'CD','THV',False,1),
    ('S6 CSE A','Saturday',4,'ACTIVITY','',False,1),
    ('S6 CSE A','Saturday',5,'CG','SPJ',False,1),
    ('S6 CSE A','Saturday',6,'CCW','AIJ',False,1),
]


# ═══════════════════════════════════════════════════
#                      MAIN
# ═══════════════════════════════════════════════════
def main():
    conn = get_conn()
    cur = conn.cursor()

    print("Seeding S6 timetables …")
    seed_batch(cur, 'S6 CSE B', S6_CSE_B_SUBJECTS, S6_CSE_B_ENTRIES)
    seed_batch(cur, 'S6 CSE A', S6_CSE_A_SUBJECTS, S6_CSE_A_ENTRIES)

    conn.commit()
    cur.close()
    conn.close()
    print("Done!")


if __name__ == "__main__":
    main()
