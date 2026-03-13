from database import get_db_connection

def check_content():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT title, content FROM website_content WHERE title ILIKE 'About us%'")
    row = cur.fetchone()
    if row:
        print(f"Title: {row[0]}")
        print(f"Content Start: {row[1][:200]}...")
    else:
        print("No 'About us' content found.")
    conn.close()

if __name__ == "__main__":
    check_content()
