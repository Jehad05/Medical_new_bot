import re
import feedparser
import requests
import logging

logger = logging.getLogger(__name__)

SOURCES = {
    "PubMed": "https://pubmed.ncbi.nlm.nih.gov/rss/search/?term=medicine&format=abstract&count=5",
    "WHO": "https://www.who.int/rss-feeds/news-english.xml",
    "BBC Health": "https://feeds.bbci.co.uk/news/health/rss.xml",
}

def clean_html(text: str) -> str:
    return re.sub(r"<[^>]+>", "", text or "").strip()

def escape_html(text: str) -> str:
    return (text.replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;"))

def fetch_feed(name: str, url: str) -> list[dict]:
    try:
        r = requests.get(url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
        r.raise_for_status()
        feed = feedparser.parse(r.content)

        articles = []
        for entry in getattr(feed, "entries", [])[:3]:
            articles.append({
                "source": name,
                "title": clean_html(entry.get("title", "No title")),
                "link": entry.get("link", ""),
                "summary": clean_html(entry.get("summary", ""))[:200],
            })
        logger.info(f"✅ {name}: {len(articles)} articles")
        return articles
    except Exception as e:
        logger.error(f"❌ {name}: {e}")
        return []

def fetch_all_news() -> list[dict]:
    out = []
    for name, url in SOURCES.items():
        out.extend(fetch_feed(name, url))
    logger.info(f"📰 Total: {len(out)}")
    return out

def format_message(articles: list[dict]) -> str:
    if not articles:
        return "⚠️ No news available at this time."

    lines = ["🏥 <b>Medical News Update</b>\n"]
    current = None
    for a in articles:
        if a["source"] != current:
            current = a["source"]
            lines.append(f"\n📌 <b>{escape_html(current)}</b>")
        lines.append(f'• <a href="{a["link"]}">{escape_html(a["title"])}</a>')
    return "\n".join(lines)
