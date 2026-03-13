import sys
import os

# Set PYTHONPATH to current directory to import 'database'
sys.path.append(os.getcwd())

from database import get_db_connection

def update_location():
    address = """Albertian Institute of Science and Technology
AISAT Technical Campus, Kalamassery
Archbishop Angel Mary Nagar,
Cochin University P. O., Kochi
Ernakulam, Kerala, India, 6820 22"""
    
    map_link = "https://maps.app.goo.gl/KjtzU1ck9Bxfxynn6"
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Add to website_content
    title = "Official AISAT Location and Address"
    content = f"The official address of AISAT is:\n{address}\n\nYou can find us on Google Maps here: {map_link}"
    
    cur.execute("DELETE FROM website_content WHERE title = %s", (title,))
    cur.execute("INSERT INTO website_content (title, content, url) VALUES (%s, %s, %s)", (title, content, map_link))
    
    print("Database updated with AISAT location.")
    
    conn.commit()
    conn.close()

if __name__ == "__main__":
    update_location()
