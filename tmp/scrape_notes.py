import requests
from bs4 import BeautifulSoup
import json

def get_notes(url):
    print(f"Scraping {url}...")
    try:
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Look for links that usually represent subjects
        # In KTUNOTES, subjects are often in H3 or list items with links
        subjects = []
        
        # Method 1: Look for links in the main content area
        # Often they are in a <div> with class like "entry-content"
        content = soup.find('div', class_='entry-content') or soup
        links = content.find_all('a')
        
        for link in links:
            text = link.get_text(strip=True)
            href = link.get('href')
            if href and ("notes" in href or "scheme" in href) and text and len(text) > 3:
                # Filter out breadcrumbs and sidebar links if possible
                if text.isupper() or any(c.isdigit() for c in text): # KTU codes often have digits
                    subjects.append({'name': text, 'url': href})
        
        return subjects
    except Exception as e:
        print(f"Error scraping {url}: {e}")
        return []

all_sem_notes = {}

# S1
all_sem_notes['S1'] = get_notes("https://www.ktunotes.in/ktu-s1-notes-2019-scheme/")
# S2
all_sem_notes['S2'] = get_notes("https://www.ktunotes.in/ktu-s2-notes-2019-scheme/")
# S3 CSE
all_sem_notes['S3'] = get_notes("https://www.ktunotes.in/ktu-s3-cse-notes-2019-scheme/")
# S4 CSE
all_sem_notes['S4'] = get_notes("https://www.ktunotes.in/ktu-s4-cse-notes-2019-scheme/")
# S5 CSE
all_sem_notes['S5'] = get_notes("https://www.ktunotes.in/ktu-s5-cse-2019-scheme-notes/")
# S6 CSE
all_sem_notes['S6'] = get_notes("https://www.ktunotes.in/ktu-s6-cse-notes-2019-scheme/")
# S7 CSE
all_sem_notes['S7'] = get_notes("https://www.ktunotes.in/ktu-s7-cse-notes-2019-scheme/")
# S8 CSE
all_sem_notes['S8'] = get_notes("https://www.ktunotes.in/ktu-s8-cse-notes-2019-scheme/")

with open('tmp/all_notes.json', 'w') as f:
    json.dump(all_sem_notes, f, indent=4)
print("Saved notes to tmp/all_notes.json")
