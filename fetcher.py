import feedparser
import requests
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# News sources RSS feeds
SOURCES = {
    "PubMed": "https://pubmed.ncbi.nlm.nih.gov/rss/search/?term=medicine&format=abstract&count=5",
    "WHO": "https://www.who.int/rss-feeds/news-english.xml",
    "BBC Health": "https://feeds.bbci.co.uk/news/health/rss.xml",
}

def fetch_feed(name: str, url: str) -> list[dict]:
    """Fetch and parse a single RSS feed."""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        feed = feedparser.parse(response.content)

        articles = []
        for entry in feed.entries[:3]:  # Max 3 articles per source
            articles.append({
                "source": name,
                "title": entry.get("title", "No title"),
                "link": entry.get("link", ""),
                "summary": entry.get("summary", "")[:200],  # First 200 chars
            })
        logger.info(f"✅ {name}: fetched {len(articles)} articles")
        return articles

    except Exception as e:
        logger.error(f"❌ {name}: failed to fetch — {e}")
        return []


def fetch_all_news() -> list[dict]:
    """Fetch news from all sources and return combined list."""
    all_articles = []
    for name, url in SOURCES.items():
        articles = fetch_feed(name, url)
        all_articles.extend(articles)

    logger.info(f"📰 Total articles fetched: {len(all_articles)}")
    return all_articles


def format_message(articles: list[dict]) -> str:
    """Format articles into a clean Telegram message."""
    if not articles:
        return "⚠️ No news available at this time."

    lines = ["🏥 *Medical News Update*\n"]

    current_source = None
    for article in articles:
        if article["source"] != current_source:
            current_source = article["source"]
            lines.append(f"\n📌 *{current_source}*")

        lines.append(f"• [{article['title']}]({article['link']})")

    return "\n".join(lines)
