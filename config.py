"""
Configuration constants for drugs.com scraper.
"""
import string

# URL patterns
BASE_URL = "https://www.drugs.com"
ALPHA_URL_TEMPLATE = BASE_URL + "/alpha/{letter}.html"
SIDE_EFFECTS_URL_TEMPLATE = BASE_URL + "/sfx/{drug_slug}-side-effects.html"

LETTERS = list(string.ascii_lowercase)  # a through z

# Browser settings
HEADLESS = True              # Set False for debugging
USER_DATA_DIR = "/tmp/drugs_scraper_profile"
BROWSER_CHANNEL = "chrome"   # Must be real Chrome, not Chromium

# Rate limiting
MIN_DELAY = 3.0   # seconds
MAX_DELAY = 7.0   # seconds
PAGE_LOAD_TIMEOUT = 30000   # milliseconds (30s)
CLOUDFLARE_WAIT = 8.0       # seconds to wait for Cloudflare challenge

# Retry settings
MAX_RETRIES = 3
RETRY_BACKOFF_BASE = 5      # seconds; exponential: 5, 10, 20

# Output paths
OUTPUT_DIR = "output"
CSV_FILE = "output/drugs_data.csv"
JSON_FILE = "output/drugs_data.json"
PROGRESS_FILE = "output/progress.json"
LOG_DIR = "logs"
LOG_FILE = "logs/scraper.log"

# CSV columns
CSV_COLUMNS = [
    'name', 'generic_name', 'url', 'description',
    'drug_class', 'rating', 'side_effects'
]
