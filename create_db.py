import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

conn = psycopg2.connect(host='localhost', dbname='postgres', user='postgres', password='1234')
conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
cursor = conn.cursor()
try:
    cursor.execute('CREATE DATABASE login')
    print("Database 'login' created successfully")
except psycopg2.errors.DuplicateDatabase:
    print("Database 'login' already exists")
cursor.close()
conn.close()
