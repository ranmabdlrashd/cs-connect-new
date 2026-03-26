import requests
from bs4 import BeautifulSoup
from database import get_db_connection
import re

# List of URLs to scrape for the CS Connect chatbot's knowledge base
URLS_TO_SCRAPE = [
    "https://www.aisat.ac.in/computer-science-and-engineering/",  # CSE Department
    "https://www.aisat.ac.in/about-us/",  # About AISAT
    "https://www.aisat.ac.in/facilities/",  # Facilities/Campus
    "https://www.aisat.ac.in/resources/",  # Resources
    "https://www.aisat.ac.in/iqac/",  # IQAC
    "https://www.aisat.ac.in/location/",  # Location
    "https://www.aisat.ac.in/research/"  # Research
]

# Keywords to filter out noise from other departments
NOISE_KEYWORDS = [
    "department of mechanical engineering", "mechanical engineering",
    "department of civil engineering", "civil engineering",
    "department of electrical and electronics engineering", "electrical engineering",
    "electrical and electronics engineering", "electronics and communication engineering",
    "department of electronics and communication engineering"
]

def is_noise(text):
    """
    Checks if a block of text contains mentions of other specific departments
    to ensure the CS Connect chatbot stays focused.
    """
    text_lower = text.lower()
    for keyword in NOISE_KEYWORDS:
        if keyword in text_lower:
            return True
    return False

def scrape_url(url):
    """
    Scrapes the given URL, extracting clean text from h1-h3 and p tags,
    skipping obvious navigation/footers, and filtering out noise.
    """
    try:
        # Add a realistic User-Agent to avoid basic blocking
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Remove noisy elements entirely before parsing text
        for element in soup(["nav", "footer", "aside", "header", "script", "style"]):
            element.decompose()

        # Extract title
        title = soup.title.string.strip() if soup.title else url

        # Extract content from headings and paragraphs
        content_pieces = []
        for tag in soup.find_all(['h1', 'h2', 'h3', 'p']):
            text = tag.get_text(separator=' ', strip=True)
            if len(text) > 20 and not is_noise(text):
                # Clean up excess whitespace
                clean_text = re.sub(r'\s+', ' ', text)
                content_pieces.append(clean_text)
                
        full_content = "\n\n".join(content_pieces)
        return title, full_content

    except Exception as e:
        print(f"Failed to scrape {url}: {e}")
        return None, None

def save_to_database(url, title, content):
    """
    Saves the extracted content into the website_content table using UPSERT logic.
    """
    if not content:
        return 0
        
    conn = get_db_connection()
    if conn is None:
        print("Database connection failed. Cannot save data.")
        return 0
        
    try:
        with conn.cursor() as cur:
            upsert_query = """
            INSERT INTO website_content (url, title, content)
            VALUES (%s, %s, %s)
            ON CONFLICT (url) DO UPDATE 
            SET title = EXCLUDED.title,
                content = EXCLUDED.content,
                scraped_at = CURRENT_TIMESTAMP;
            """
            cur.execute(upsert_query, (url, title, content))
            conn.commit()
            return len(content)
    except Exception as e:
        print(f"Error saving data for {url} to database: {e}")
        conn.rollback()
        return 0
    finally:
        conn.close()

def main():
    print("Starting CS Connect Data Ingestion Phase 2...\n")
    
    total_saved = 0
    successful_urls = 0
    
    for url in URLS_TO_SCRAPE:
        print(f"Scraping: {url}...")
        title, content = scrape_url(url)
        
        if title and content:
            chars_saved = save_to_database(url, title, content)
            if chars_saved > 0:
                print(f"  -> SUCCESS: Saved '{title}' ({chars_saved} characters).")
                total_saved += chars_saved
                successful_urls += 1
            else:
                print(f"  -> FAILED: Could not save data to database.")
        else:
            print(f"  -> SKIPPED: No usable content extracted.")
            
    print("\n" + "="*50)
    print("INGESTION SUMMARY")
    print(f"Total URLs successfully scraped: {successful_urls} / {len(URLS_TO_SCRAPE)}")
    print(f"Total characters stored in database: {total_saved}")
    print("="*50)

if __name__ == "__main__":
    main()
