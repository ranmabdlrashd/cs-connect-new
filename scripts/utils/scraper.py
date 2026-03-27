import requests
from bs4 import BeautifulSoup
from database import db_connection
import re
import logging

# Setup module-level logger
logger = logging.getLogger(__name__)

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

    except Exception:
        logger.exception("Failed to scrape URL: %s", url)
        return None, None

def save_to_database(url, title, content):
    """
    Saves the extracted content into the website_content table using UPSERT logic.
    """
    if not content:
        return 0
        
    try:
        with db_connection() as conn:
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
    except Exception:
        logger.exception("Error saving data for %s to database", url)
        return 0

def main():
    logger.info("Starting CS Connect Data Ingestion Phase 2...")
    
    total_saved = 0
    successful_urls = 0
    
    for url in URLS_TO_SCRAPE:
        logger.info("Scraping: %s...", url)
        title, content = scrape_url(url)
        
        if title and content:
            chars_saved = save_to_database(url, title, content)
            if chars_saved > 0:
                logger.info("  -> SUCCESS: Saved '%s' (%d characters).", title, chars_saved)
                total_saved += chars_saved
                successful_urls += 1
            else:
                logger.error("  -> FAILED: Could not save data to database.")
        else:
            logger.warning("  -> SKIPPED: No usable content extracted.")
            
    logger.info("INGESTION SUMMARY")
    logger.info("Total URLs successfully scraped: %d / %d", successful_urls, len(URLS_TO_SCRAPE))
    logger.info("Total characters stored in database: %d", total_saved)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    main()
