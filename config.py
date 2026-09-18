"""Central configuration for the Medical News Bot."""
import os

# ─── Sources ─────────────────────────────────────────────
SOURCES = {
    "PubMed": "https://pubmed.ncbi.nlm.nih.gov/rss/search/?term=medicine&format=abstract&count=5",
    "WHO": "https://www.who.int/rss-feeds/news-english.xml",
    "BBC Health": "https://feeds.bbci.co.uk/news/health/rss.xml",
}

# ─── Fetching ────────────────────────────────────────────
MAX_ARTICLES_PER_SOURCE = int(os.getenv("MAX_PER_SOURCE", "3"))
MAX_ARTICLE_AGE_HOURS = int(os.getenv("MAX_AGE_HOURS", "24"))
TIMEOUTS = {
    "PubMed": 10,
    "WHO": 20,
    "BBC Health": 8,
}
DEFAULT_TIMEOUT = 15

# ─── Retry ───────────────────────────────────────────────
RETRY_TOTAL = 3
RETRY_BACKOFF = 1
RETRY_STATUS = [429, 500, 502, 503, 504]

# ─── Storage ─────────────────────────────────────────────
DB_PATH = os.getenv("DB_PATH", "/data/seen.db")
SEEN_RETENTION_DAYS = 7
MAX_ROWS = 10000  # Hard cap for safety

# ─── Telegram ────────────────────────────────────────────
MAX_MESSAGE_LENGTH = 4000
SEND_DELAY_SECONDS = 1

# ─── Misc ────────────────────────────────────────────────
HASHTAGS = "\n\n#MedicalNews #Health #WHO #PubMed #BBCHealth"
