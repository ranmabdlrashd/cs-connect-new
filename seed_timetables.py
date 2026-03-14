"""
Seed script: insert S4 CSE A, S2 CSE B, S8 CSE, S4 CSE B timetables.
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
#                S4 CSE A  (Room A406)
# ═══════════════════════════════════════════════════
S4_CSE_A_SUBJECTS = [
    ('S4 CSE A', 'MAT-4',   'GAMAT401 Mathematics for Computer And Information Science-4', 'SDC', 'Prof. Shereeta D\'coutha'),
    ('S4 CSE A', 'DBMS',    'PCCST402 Database Management Systems',                        'SHC', 'Prof. Shruthi Chandran'),
    ('S4 CSE A', 'OS',      'PCCST403 Operating Systems',                                  'NJP', 'Prof. Nisy John Panicker'),
    ('S4 CSE A', 'COA',     'PBCST404 Computer Organization and Architecture',              'KCJ', 'Prof. Krishna C J'),
    ('S4 CSE A', 'SE',      'PECST411 Software Engineering',                                'ANG', 'Prof. Angel Mathai'),
    ('S4 CSE A', 'EESD',    'UCHUT347 Engineering Ethics and Sustainable Development',      'NIJ', 'Prof. Nithya John'),
    ('S4 CSE A', 'OS LAB',  'PCCSL407 Operating Systems Lab',                               'NJP,NF', 'Prof. Nisy John Panicker, New Faculty'),
    ('S4 CSE A', 'DBMS LAB','PCCSL408 DBMS Lab',                                            'TEJ,SHC', 'Prof. Teenu Jose, Prof. Shruthy Chandran'),
    ('S4 CSE A', 'ACTIVITY','Activity Hour',                                                 '',    ''),
]

S4_CSE_A_ENTRIES = [
    # MONDAY
    ('S4 CSE A','Monday',1,'DBMS','SHC',False,1),
    ('S4 CSE A','Monday',2,'EESD','NIJ',False,1),
    ('S4 CSE A','Monday',3,'OS','NJP',False,1),
    ('S4 CSE A','Monday',4,'MAT-4','SDC',False,1),
    ('S4 CSE A','Monday',5,'COA(R)','KCJ',False,1),
    ('S4 CSE A','Monday',6,'SE','ANG',False,1),
    # TUESDAY
    ('S4 CSE A','Tuesday',1,'COA','KCJ',False,1),
    ('S4 CSE A','Tuesday',2,'OS(R)','NJP',False,1),
    ('S4 CSE A','Tuesday',3,'COA','KCJ',False,1),
    ('S4 CSE A','Tuesday',4,'SE','ANG',False,1),
    ('S4 CSE A','Tuesday',5,'MAT-4','SDC',False,1),
    ('S4 CSE A','Tuesday',6,'DBMS','SHC',False,1),
    # WEDNESDAY
    ('S4 CSE A','Wednesday',1,'MAT-4','SDC',False,1),
    ('S4 CSE A','Wednesday',2,'OS','NJP',False,1),
    ('S4 CSE A','Wednesday',3,'DBMS(T)','SHC',False,1),
    ('S4 CSE A','Wednesday',5,'OS LAB/DBMS LAB','NJP/TEJ',True,2),
    # THURSDAY
    ('S4 CSE A','Thursday',1,'COA','KCJ',False,1),
    ('S4 CSE A','Thursday',2,'DBMS(R)','SHC',False,1),
    ('S4 CSE A','Thursday',3,'OS','NJP',False,1),
    ('S4 CSE A','Thursday',5,'OS LAB/DBMS LAB','NF/SHC',True,2),
    # FRIDAY
    ('S4 CSE A','Friday',1,'SE(R)','ANG',False,1),
    ('S4 CSE A','Friday',2,'COA','KCJ',False,1),
    ('S4 CSE A','Friday',3,'EESD','NIJ',False,1),
    ('S4 CSE A','Friday',4,'OS(T)','NJP',False,1),
    ('S4 CSE A','Friday',5,'MAT-4','SDC',False,1),
    ('S4 CSE A','Friday',6,'DBMS','SHC',False,1),
    # SATURDAY
    ('S4 CSE A','Saturday',1,'SE','ANG',False,1),
    ('S4 CSE A','Saturday',2,'OS','NJP',False,1),
    ('S4 CSE A','Saturday',3,'COA','KCJ',False,1),
    ('S4 CSE A','Saturday',4,'ACTIVITY','',False,1),
    ('S4 CSE A','Saturday',5,'SE','ANG',False,1),
    ('S4 CSE A','Saturday',6,'DBMS','SHC',False,1),
]


# ═══════════════════════════════════════════════════
#                S2 CSE B  (Room A214)
# ═══════════════════════════════════════════════════
S2_CSE_B_SUBJECTS = [
    ('S2 CSE B', 'MAT-2',   'GAMAT201 Mathematics for Information Science - 2',             'DGP', 'Prof. Dhanya George P'),  # SDC in image, but using DGP based on existing S2 CSE A
    ('S2 CSE B', 'PHY',     'GAPHT121 Physics for Information Science',                      'REK', 'Prof. Reshma K J'),
    ('S2 CSE B', 'FOC',     'GXEST203 Foundations of Computing: From Hardware Essentials to Web Design', 'SWC', 'Prof. Sweety Joy C'),
    ('S2 CSE B', 'CP',      'GXEST204 Programming in C',                                    'SPM,KRC', 'Prof. Sharija P M, Prof. Krishna C J'),
    ('S2 CSE B', 'DMS',     'PCCST205 Discrete Mathematics',                                'AAF', 'Prof. Anson Antony Fertal'),  # AFF in image
    ('S2 CSE B', 'IPR',     'UCEST206 Engineering Entrepreneurship & IPR',                   'ANS', 'Prof. Anagha S'),
    ('S2 CSE B', 'HW',      'UCHWT127 Health and Wellness',                                 'DMR', 'Prof. Dilu Mary Rose'),
    ('S2 CSE B', 'IT W/S',  'GXESL208 IT Workshop',                                         'SWC', 'Prof. Sweety Joy C'),
    ('S2 CSE B', 'LT',      'Language Training',                                             'DMR', 'Prof. Dilu Mary Rose'),
    ('S2 CSE B', 'ACTIVITY','Activity Hour',                                                  'SWC,RPL,ANG', 'Prof. Sweety Joy C, Prof. Rose Paul, Prof. Angel Mathai'),
    ('S2 CSE B', 'CP/PHY LAB','CP / Physics Lab (Combined)',                                 'SPM,KRC,REK', 'Prof. Sharija P M, Prof. Krishna C J, Prof. Reshma K J'),
    ('S2 CSE B', 'IT W/S/PHY LAB','IT Workshop / Physics Lab (Combined)',                    'SWC,SRC', 'Prof. Sweety Joy C, Prof. Sreeja C'),
    ('S2 CSE B', 'CP/IT W/S','Programming in C / IT Workshop (Combined)',                    'SPM,KRC,SWC', 'Prof. Sharija P M, Prof. Krishna C J, Prof. Sweety Joy C'),
    ('S2 CSE B', 'DMS(T)',  'Discrete Mathematics Tutorial',                                  'AAF', 'Prof. Anson Antony Fertal'),
    ('S2 CSE B', 'HW(P)',   'Health and Wellness (Practical)',                                'DMR', 'Prof. Dilu Mary Rose'),
]

S2_CSE_B_ENTRIES = [
    # MONDAY
    ('S2 CSE B','Monday',1,'PHY','REK',False,1),
    ('S2 CSE B','Monday',2,'DMS','AAF',False,1),
    ('S2 CSE B','Monday',3,'CP/PHY LAB','SPM,KRC,REK',True,2),
    ('S2 CSE B','Monday',5,'FOC','SWC',False,1),
    ('S2 CSE B','Monday',6,'MAT-2','DGP',False,1),
    # TUESDAY
    ('S2 CSE B','Tuesday',1,'IPR','ANS',False,1),
    ('S2 CSE B','Tuesday',2,'FOC','SWC',False,1),
    ('S2 CSE B','Tuesday',3,'HW','DMR',False,1),
    ('S2 CSE B','Tuesday',4,'CP','SPM',False,1),
    ('S2 CSE B','Tuesday',5,'IT W/S/PHY LAB','SWC,SRC',True,2),
    # WEDNESDAY
    ('S2 CSE B','Wednesday',1,'CP/IT W/S','SPM,KRC,SWC',True,2),
    ('S2 CSE B','Wednesday',3,'MAT-2','DGP',False,1),
    ('S2 CSE B','Wednesday',4,'IPR','ANS',False,1),
    ('S2 CSE B','Wednesday',5,'PHY','REK',False,1),
    ('S2 CSE B','Wednesday',6,'HW(P)','DMR',False,1),
    # THURSDAY
    ('S2 CSE B','Thursday',1,'FOC','SWC',False,1),
    ('S2 CSE B','Thursday',2,'MAT-2','DGP',False,1),
    ('S2 CSE B','Thursday',3,'DMS','AAF',False,1),
    ('S2 CSE B','Thursday',4,'PHY','REK',False,1),
    ('S2 CSE B','Thursday',5,'CP','SPM',False,1),
    ('S2 CSE B','Thursday',6,'CP','SPM',False,1),
    # FRIDAY
    ('S2 CSE B','Friday',1,'MAT-2','DGP',False,1),
    ('S2 CSE B','Friday',2,'CP','SPM',False,1),
    ('S2 CSE B','Friday',3,'DMS','AAF',False,1),
    ('S2 CSE B','Friday',4,'LT','DMR',False,1),
    ('S2 CSE B','Friday',5,'IPR','ANS',False,1),
    ('S2 CSE B','Friday',6,'DMS(T)','AAF',False,1),
    # SATURDAY
    ('S2 CSE B','Saturday',1,'DMS','AAF',False,1),
    ('S2 CSE B','Saturday',2,'CP','SPM',False,1),
    ('S2 CSE B','Saturday',3,'FOC','SWC',False,1),
    ('S2 CSE B','Saturday',4,'ACTIVITY','SWC,RPL,ANG',False,1),
    ('S2 CSE B','Saturday',5,'HW','DMR',False,1),
    ('S2 CSE B','Saturday',6,'PHY','REK',False,1),
]


# ═══════════════════════════════════════════════════
#                S8 CSE
# ═══════════════════════════════════════════════════
S8_CSE_SUBJECTS = [
    ('S8 CSE', 'DC',      'CST402 Distributed Computing',           'NJP', 'Prof. Nisy John Panicker'),
    ('S8 CSE', 'CCV',     'CST404 Comprehensive Course Viva',       'AIJ', 'Prof. Anna Isabel John'),
    ('S8 CSE', 'NSP',     'CST424 Network Security Protocol',       'NF',  'New Faculty'),
    ('S8 CSE', 'CSA',     'CST426 Client Server Architecture',      'AIJ', 'Prof. Anna Isabel John'),
    ('S8 CSE', 'DM',      'CST466 Data Mining',                     'DIM', 'Prof. Divya Mohan'),
    ('S8 CSE', 'BCT',     'CST428 Blockchain Technologies',         'JRD', 'Dr. Jeswin Roy DCouth'),
    ('S8 CSE', 'IOT',     'CST448 Internet Of Things',              'SWC', 'Prof. Sweety Joy C'),
    ('S8 CSE', 'PROJECT', 'CSD416 Project Phase II',                'JRD,DIM', 'Dr. Jeswin Roy DCouth, Prof. Divya Mohan'),
    ('S8 CSE', 'DM/CSA',  'Data Mining / Client Server Architecture (Combined)', 'DIM,AIJ', 'Prof. Divya Mohan, Prof. Anna Isabel John'),
    ('S8 CSE', 'BCT/IOT', 'Blockchain Technologies / Internet Of Things (Combined)', 'JRD,SWC', 'Dr. Jeswin Roy DCouth, Prof. Sweety Joy C'),
]

S8_CSE_ENTRIES = [
    # MONDAY
    ('S8 CSE','Monday',1,'NSP','NF',False,1),
    ('S8 CSE','Monday',2,'DC','NJP',False,1),
    ('S8 CSE','Monday',3,'DM/CSA','DIM,AIJ',False,1),
    ('S8 CSE','Monday',4,'BCT/IOT','JRD,SWC',False,1),
    ('S8 CSE','Monday',5,'PROJECT','DIM,JRD',True,2),
    # TUESDAY
    ('S8 CSE','Tuesday',1,'BCT/IOT','JRD,SWC',True,1),
    ('S8 CSE','Tuesday',2,'DM/CSA','DIM,AIJ',True,1),
    ('S8 CSE','Tuesday',3,'DC','NJP',False,1),
    ('S8 CSE','Tuesday',4,'NSP','NF',False,1),
    ('S8 CSE','Tuesday',5,'NSP(R)','NF',False,1),
    ('S8 CSE','Tuesday',6,'CCV','ANG',False,1),
    # WEDNESDAY
    ('S8 CSE','Wednesday',2,'PROJECT','DIM',True,1),
    ('S8 CSE','Wednesday',4,'NSP(T)','NF',False,1),
    ('S8 CSE','Wednesday',5,'BCT/IOT','JRD,SWC',False,1),
    ('S8 CSE','Wednesday',6,'BCT/IOT(T)','JRD,SWC',False,1),
    # THURSDAY
    ('S8 CSE','Thursday',1,'DC','NJP',False,1),
    ('S8 CSE','Thursday',2,'DC(R)','NJP',False,1),
    ('S8 CSE','Thursday',3,'NSP','NF',False,1),
    ('S8 CSE','Thursday',4,'CCV','ANG',False,1),
    ('S8 CSE','Thursday',5,'DM/CSA','DIM,AIJ',False,1),
    ('S8 CSE','Thursday',6,'DM/CSA(R)','DIM,AIJ',False,1),
    # FRIDAY
    ('S8 CSE','Friday',1,'DM/CSA(T)','DIM,AIJ',True,1),
    ('S8 CSE','Friday',2,'DC(T)','NJP',False,1),
    ('S8 CSE','Friday',3,'BCT/IOT(R)','JRD,SWC',True,1),
    ('S8 CSE','Friday',5,'PROJECT','JRD',True,2),
    # SATURDAY
    ('S8 CSE','Saturday',3,'PROJECT','JRD,DIM',True,4),
]


# ═══════════════════════════════════════════════════
#                S4 CSE B  (Room A414)
# ═══════════════════════════════════════════════════
S4_CSE_B_SUBJECTS = [
    ('S4 CSE B', 'MAT-4',   'GAMAT401 Mathematics for Computer And Information Science-4', 'SDC', 'Prof. Shereeta D\'coutha'),
    ('S4 CSE B', 'DBMS',    'PCCST402 Database Management Systems',                        'SPJ', 'Prof. Sinijoy P J'),
    ('S4 CSE B', 'OS',      'PCCST403 Operating Systems',                                  'SHC', 'Prof. Shruthi Chandran'),
    ('S4 CSE B', 'COA',     'PBCST404 Computer Organization and Architecture',              'AIJ', 'Prof. Anna Isabel John'),
    ('S4 CSE B', 'SE',      'PECST411 Software Engineering',                                'ANG', 'Prof. Angel Mathai'),
    ('S4 CSE B', 'EESD',    'UCHUT347 Engineering Ethics and Sustainable Development',      'AKR', 'Prof. Asha K R'),
    ('S4 CSE B', 'OS LAB',  'PCCSL407 Operating Systems Lab',                               'SHC', 'Prof. Shruthi Chandran'),
    ('S4 CSE B', 'DBMS LAB','PCCSL408 DBMS Lab',                                            'SPJ,KRC', 'Prof. Sinijoy P J, Prof. Krishna C J'),
    ('S4 CSE B', 'ACTIVITY','Activity Hour',                                                 '',    ''),
]

S4_CSE_B_ENTRIES = [
    # MONDAY
    ('S4 CSE B','Monday',1,'COA','AIJ',False,1),
    ('S4 CSE B','Monday',2,'DBMS(R)','SPJ',False,1),
    ('S4 CSE B','Monday',3,'OS','SHC',False,1),
    ('S4 CSE B','Monday',5,'OS LAB/DBMS LAB','SHC/SPJ',True,2),
    # TUESDAY
    ('S4 CSE B','Tuesday',1,'DBMS(T)','SPJ',False,1),
    ('S4 CSE B','Tuesday',2,'MAT-4','SDC',False,1),
    ('S4 CSE B','Tuesday',3,'COA','AIJ',False,1),
    ('S4 CSE B','Tuesday',5,'OS LAB/DBMS LAB','SHC/KRC',True,2),
    # WEDNESDAY
    ('S4 CSE B','Wednesday',1,'OS(T)','SHC',False,1),
    ('S4 CSE B','Wednesday',2,'COA','AIJ',False,1),
    ('S4 CSE B','Wednesday',3,'MAT-4','SDC',False,1),
    ('S4 CSE B','Wednesday',4,'OS','SHC',False,1),
    ('S4 CSE B','Wednesday',5,'SE(R)','ANG',False,1),
    ('S4 CSE B','Wednesday',6,'EESD','AKR',False,1),
    # THURSDAY
    ('S4 CSE B','Thursday',1,'DBMS','SPJ',False,1),
    ('S4 CSE B','Thursday',2,'DBMS','SPJ',False,1),
    ('S4 CSE B','Thursday',3,'OS(R)','SHC',False,1),
    ('S4 CSE B','Thursday',4,'COA','AIJ',False,1),
    ('S4 CSE B','Thursday',5,'SE','ANG',False,1),
    ('S4 CSE B','Thursday',6,'MAT-4','SDC',False,1),
    # FRIDAY
    ('S4 CSE B','Friday',1,'EESD','AKR',False,1),
    ('S4 CSE B','Friday',2,'MAT-4','SDC',False,1),
    ('S4 CSE B','Friday',3,'DBMS','SPJ',False,1),
    ('S4 CSE B','Friday',4,'OS','SHC',False,1),
    ('S4 CSE B','Friday',5,'SE','ANG',False,1),
    ('S4 CSE B','Friday',6,'COA(R)','AIJ',False,1),
    # SATURDAY
    ('S4 CSE B','Saturday',1,'OS','SHC',False,1),
    ('S4 CSE B','Saturday',2,'DBMS','SPJ',False,1),
    ('S4 CSE B','Saturday',3,'SE','ANG',False,1),
    ('S4 CSE B','Saturday',4,'ACTIVITY','',False,1),
    ('S4 CSE B','Saturday',5,'COA','AIJ',False,1),
    ('S4 CSE B','Saturday',6,'SE','ANG',False,1),
]


# ═══════════════════════════════════════════════════
#                      MAIN
# ═══════════════════════════════════════════════════
def main():
    conn = get_conn()
    cur = conn.cursor()

    print("Seeding timetables …")
    seed_batch(cur, 'S4 CSE A', S4_CSE_A_SUBJECTS, S4_CSE_A_ENTRIES)
    seed_batch(cur, 'S2 CSE B', S2_CSE_B_SUBJECTS, S2_CSE_B_ENTRIES)
    seed_batch(cur, 'S8 CSE',   S8_CSE_SUBJECTS,   S8_CSE_ENTRIES)
    seed_batch(cur, 'S4 CSE B', S4_CSE_B_SUBJECTS, S4_CSE_B_ENTRIES)

    conn.commit()
    cur.close()
    conn.close()
    print("Done!")


if __name__ == "__main__":
    main()
