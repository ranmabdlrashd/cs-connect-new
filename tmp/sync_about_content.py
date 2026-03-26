import os
import re
import sys

# Ensure the root directory is in sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database import get_db_connection

def clean_html(raw_html):
    """Basic HTML tag stripping with some newline preservation."""
    cleanr = re.compile('<.*?>')
    # Replace block level tags with newlines to preserve structure
    raw_html = re.sub(r'<(p|div|h1|h2|h3|li|section|header|footer|br).*?>', r'\n', raw_html)
    cleantext = re.sub(cleanr, '', raw_html)
    # Collapse multiple newlines
    cleantext = re.sub(r'\n\s*\n+', '\n\n', cleantext)
    return cleantext.strip()

def sync_page(title, template_path):
    print(f"Syncing: {title} from {template_path}...")
    
    if not os.path.exists(template_path):
        print(f"Error: Template {template_path} not found.")
        return

    with open(template_path, 'r', encoding='utf-8') as f:
        html_content = f.read()

    # Extract the main content (rough heuristic)
    # Removing Jinja tags
    html_content = re.sub(r'\{%.*?%\}', '', html_content)
    html_content = re.sub(r'\{\{.*?\}\}', '', html_content)
    
    plain_text = clean_html(html_content)

    conn = get_db_connection()
    if not conn:
        print("Database connection failed.")
        return

    try:
        with conn.cursor() as cur:
            # Check if exists
            cur.execute("SELECT id FROM website_content WHERE title = %s", (title,))
            row = cur.fetchone()
            
            if row:
                cur.execute(
                    "UPDATE website_content SET content = %s, scraped_at = CURRENT_TIMESTAMP WHERE id = %s",
                    (plain_text, row[0])
                )
                print(f"Updated '{title}' in database.")
            else:
                url = f"/about/{title.lower().replace(' ', '-')}"
                cur.execute(
                    "INSERT INTO website_content (url, title, content) VALUES (%s, %s, %s)",
                    (url, title, plain_text)
                )
                print(f"Inserted '{title}' into database.")
            
            conn.commit()
    except Exception as e:
        print(f"Database error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    # Sync About AISAT
    sync_page("About us – AISAT Engineering College", "templates/about/about-aisat.html")
    # Sync About CSE
    sync_page("AISAT CSE Department Overview", "templates/about/about-cse.html")
    # Sync Syllabus
    sync_page("AISAT CSE Curriculum and Syllabus", "templates/about/about-cse.html") # Reuse for now or points to same
    
    print("\nSync complete.")
