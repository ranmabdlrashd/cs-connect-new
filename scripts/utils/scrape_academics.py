"""
AISAT Academics Scraper
Scrapes CSE-focused academic content from AISAT's website and PDFs,
then injects it into the website_content database table.

Sources:
- CSE Department page (HTML)
- Programs overview page (HTML)
- Controller of Examinations page (HTML)
- Academic Handbook 2025-26 (PDF)
- CSE Student Handout / Curriculum (PDF)

Filtered to remove: Civil, Mechanical, Electrical, Electronics, Polytechnic content.
"""

import os
import sys
import io
import requests
from bs4 import BeautifulSoup
from pypdf import PdfReader
from dotenv import load_dotenv

# Force UTF-8 output
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Add project root for database import
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
load_dotenv()

from database import get_db_connection

# ─────────────────────────────────────────────
# Config
# ─────────────────────────────────────────────
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}

# Keywords that flag content as belonging to OTHER departments
EXCLUDE_DEPARTMENTS = [
    "civil engineering", "ce department", "mechanical engineering",
    "me department", "electrical and electronics", "eee department",
    "electronics and communication", "ece department", "polytechnic",
    "applied science", "humanities", "artificial intelligence and machine learning",
    "ai & ml department", "ai&ml",
]

# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────
def is_cse_relevant(text: str) -> bool:
    """Returns True if the paragraph does NOT belong to another dept."""
    lower = text.lower()
    for excl in EXCLUDE_DEPARTMENTS:
        if excl in lower:
            return False
    return True


def clean_text(text: str) -> str:
    """Remove extra whitespace from text."""
    return " ".join(text.split())


def fetch_html_text(url: str, section_filter: str | None = None) -> str:
    """Fetch an HTML page and extract visible text."""
    print(f"  [HTML] Fetching: {url}")
    try:
        resp = requests.get(url, headers=HEADERS, timeout=20)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        # Remove nav, scripts, footer, sidebar clutter
        for tag in soup.select("nav, script, style, footer, header, .widget, .sidebar, iframe"):
            tag.decompose()

        # Get all paragraph-like blocks
        paragraphs = soup.find_all(["p", "li", "h2", "h3", "h4", "td"])
        collected = []
        for p in paragraphs:
            text = clean_text(p.get_text())
            if len(text) > 20 and is_cse_relevant(text):
                collected.append(text)

        return "\n".join(collected)
    except Exception as e:
        print(f"  [ERROR] Could not fetch {url}: {e}")
        return ""


def fetch_pdf_text(url: str) -> str:
    """Download a PDF from a URL and extract its text content."""
    print(f"  [PDF] Fetching: {url}")
    try:
        resp = requests.get(url, headers=HEADERS, timeout=60)
        resp.raise_for_status()
        pdf_bytes = io.BytesIO(resp.content)
        reader = PdfReader(pdf_bytes)

        all_text = []
        for i, page in enumerate(reader.pages):
            page_text = page.extract_text() or ""
            # Filter out paragraphs about other departments
            for para in page_text.split("\n"):
                if len(para.strip()) > 15 and is_cse_relevant(para):
                    all_text.append(para.strip())

        result = "\n".join(all_text)
        print(f"    → Extracted {len(reader.pages)} pages, {len(result)} chars")
        return result
    except Exception as e:
        print(f"  [ERROR] Could not fetch PDF {url}: {e}")
        return ""


def save_to_db(conn, title: str, url: str, content: str):
    """Insert or replace a record in website_content."""
    if not content.strip():
        print(f"  [SKIP] No content for: {title}")
        return

    cur = conn.cursor()
    cur.execute("DELETE FROM website_content WHERE title = %s", (title,))
    cur.execute(
        "INSERT INTO website_content (title, url, content) VALUES (%s, %s, %s)",
        (title, url, content[:50000])  # cap at 50k chars
    )
    conn.commit()
    print(f"  [DB]   Saved '{title}' ({len(content)} chars)")


# ─────────────────────────────────────────────
# Main scraping jobs
# ─────────────────────────────────────────────
def scrape_all():
    conn = get_db_connection()
    print("\n=== AISAT Academics Scraper ===\n")

    # 1. CSE Department Page
    print("[1/5] CSE Department Overview")
    cse_page_text = fetch_html_text("https://aisat.ac.in/departments/computer-science-engineering/")
    save_to_db(conn,
               "AISAT CSE Department Overview",
               "https://aisat.ac.in/departments/computer-science-engineering/",
               cse_page_text)

    # 2. General Academic Programs Page
    print("[2/5] Academic Programs Overview")
    programs_text = fetch_html_text("https://aisat.ac.in/about-us/our-programs/")
    save_to_db(conn,
               "AISAT Academic Programs",
               "https://aisat.ac.in/about-us/our-programs/",
               programs_text)

    # 3. Controller of Examinations Page
    print("[3/5] Controller of Examinations")
    exam_text = fetch_html_text("https://aisat.ac.in/about-us/controller-of-examinations/")
    save_to_db(conn,
               "AISAT Controller of Examinations",
               "https://aisat.ac.in/about-us/controller-of-examinations/",
               exam_text)

    # 4. Academic Handbook PDF (contains exam rules, academic calendar, fee structure, etc.)
    print("[4/5] Academic Handbook 2025-26 (PDF)")
    handbook_text = fetch_pdf_text(
        "https://aisat.ac.in/wp-content/uploads/2025/12/Handbook-2025-26_compressed.pdf"
    )
    save_to_db(conn,
               "AISAT Academic Handbook 2025-26",
               "https://aisat.ac.in/wp-content/uploads/2025/12/Handbook-2025-26_compressed.pdf",
               handbook_text)

    # 5. CSE Student Handout PDF (curriculum, syllabus, course outcomes)
    print("[5/5] CSE Student Handout / Curriculum & Syllabus (PDF)")
    handout_text = fetch_pdf_text(
        "https://aisat.ac.in/wp-content/uploads/2025/11/CSE_Handout.pdf"
    )
    save_to_db(conn,
               "AISAT CSE Curriculum and Syllabus",
               "https://aisat.ac.in/wp-content/uploads/2025/11/CSE_Handout.pdf",
               handout_text)

    conn.close()
    print("\n=== Scraping Complete! ===\n")


if __name__ == "__main__":
    scrape_all()
