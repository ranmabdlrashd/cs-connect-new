"""Seed the mous table with 13 MOU entries."""
import os, psycopg2
from dotenv import load_dotenv
load_dotenv()

db_url = (os.environ.get("NEON_DATABASE_URL")
          or os.environ.get("LOCAL_DATABASE_URL")
          or os.environ.get("DATABASE_URL"))
conn = psycopg2.connect(db_url)
cur = conn.cursor()

# Create table if not exists
cur.execute('''
    CREATE TABLE IF NOT EXISTS mous (
        id SERIAL PRIMARY KEY,
        organization TEXT NOT NULL,
        date_of_signing TEXT,
        status TEXT DEFAULT 'Active'
    )
''')

# Only seed if empty
cur.execute("SELECT COUNT(*) FROM mous")
if cur.fetchone()[0] == 0:
    mous = [
        ('RedTeam Hacker Academy',                                              '18-02-2026', 'Active'),
        ('Volador Aerospace Pvt Ltd',                                           '18-02-2026', 'Active'),
        ('Kerala State Information Technology Infrastructure Limited, Thiruvananthapuram', '30-01-2026', 'Active'),
        ('Archon Solutions Private Limited',                                     '22-10-2025', 'Active'),
        ('NEST Pvt Ltd',                                                         '24-09-2025', 'Active'),
        ('ICT Academy of Kerala',                                                '19-09-2025', 'Active'),
        ('Additional Skill Acquisition Programme Kerala (ASAP)',                 '01-01-2025', 'Active'),
        ('NAVA Design & Innovation Pvt. Ltd',                                   '19-10-2023', 'Active'),
        ('Mind Empowered, Kochi',                                                '17-01-2023', 'Active'),
        ('Tekosol IT Solutions, Bangalore',                                      '31-08-2022', 'Active'),
        ('Vedant IT Solutions, Kochi',                                           '31-08-2022', 'Active'),
        ('Revertech IT Solutions Pvt Ltd, Kochi',                               '04-04-2022', 'Active'),
        ('Kerala State Information Technology Infrastructure Limited, Thiruvananthapuram', '07-12-2021', 'Active'),
    ]
    cur.executemany(
        "INSERT INTO mous (organization, date_of_signing, status) VALUES (%s, %s, %s)",
        mous,
    )
    print(f"✅ Seeded {len(mous)} MOUs")
else:
    print("⏭  MOUs already exist — skipping.")

conn.commit()
cur.close()
conn.close()
print("Done!")
