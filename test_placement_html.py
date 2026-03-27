import urllib.request
import logging

# Setup module-level logger
logger = logging.getLogger(__name__)

def run_test():
    try:
        with urllib.request.urlopen("http://127.0.0.1:5000/placements") as response:
            html = response.read().decode('utf-8')
            logger.info("CSS Link: %s", "placement.css" in html)
            logger.info("CSS Link (Plural): %s", "placements.css" in html)
            logger.info("JS Link: %s", "placement.js" in html)
            logger.info("JS Link (Plural): %s", "placements.js" in html)
            # Find the line with the CSS link
            for line in html.split('\n'):
                if "placement" in line:
                    logger.info("Found: %s", line.strip())
    except Exception:
        logger.exception("Error during HTML test")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    run_test()
