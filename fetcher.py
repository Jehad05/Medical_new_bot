import re
import feedparser
import requests
import logging
from datetime import datetime, timezone
import email.utils

logger = logging.getLogger(__name__)

SOURCES = {
    "PubMed": "https://pubmed.ncbi.nlm.nih.gov/rss/search/?term=medicine&format=abstract&count=5",
    "WHO": "https://www.who.int/rss-feeds/news-english.xml",
    "BBC Health": "https://feeds.bbci.co.uk/news/health/rss.xml",
}

HASHTAGS = "\n\n#MedicalNews #Health #WHO #PubMed #BBCHealth"


def clean_html(text: str) -> str:
    return re.sub(r"<[^>]+>", "", text or "").strip()


def escape_html(text: str) -> str:
    return (text.replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;"))


def time_ago(entry) -> str:
    """Return human-readable time since publication."""
    try:
        published = entry.get("published", "") or entry.get("updated", "")
        if not published:
            return ""
        parsed = email.utils.parsedate_to_datetime(published)
        now = datetime.now(timezone.utc)
        diff = now - parsed
        minutes = int(diff.total_seconds() / 60)

        if minutes < 60:
            return f"🕐 {minutes}m ago"
        elif minutes < 1440:
            return f"🕐 {minutes // 60}h ago"
        else:
            return f"🕐 {minutes // 1440}d ago"
    except Exception:
        return ""


def fetch_feed(name: str, url: str) -> list[dict]:
    try:
        r = requests.get(url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
        r.raise_for_status()
        feed = feedparser.parse(r.content)

        articles = []
        for entry in getattr(feed, "entries", [])[:3]:
            summary = clean_html(entry.get("summary", ""))
            # trim to last complete word within 200 chars
            if len(summary) > 200:
                summary = summary[:200].rsplit(" ", 1)[0] + "..."

            articles.append({
                "source": name,
                "title": clean_html(entry.get("title", "No title")),
                "link": entry.get("link", ""),
                "summary": summary,
                "time_ago": time_ago(entry),
            })
        logger.info(f"✅ {name}: {len(articles)} articles")
        return articles
    except Exception as e:
        logger.error(f"❌ {name}: {e}")
        return []


def fetch_all_news() -> dict[str, list[dict]]:
    """Return dict of source -> articles."""
    result = {}
    for name, url in SOURCES.items():
        articles = fetch_feed(name, url)
        if articles:
            result[name] = articles
    total = sum(len(v) for v in result.values())
    logger.info(f"📰 Total: {total} articles from {len(result)} sources")
    return result


def format_messages(news: dict[str, list[dict]]) -> list[str]:
    """Return one message per source."""
    if not news:
        return ["⚠️ No news available at this time."]

    messages = []
    total = sum(len(v) for v in news.items())

    for source, articles in news.items():
        lines = [
            f"🏥 <b>Medical News Update</b>",
            f"📊 {len(articles)} articles · {source}",
            "━━━━━━━━━━━━━━━━━━━━",
        ]

        for a in articles:
            lines.append(f'\n• <a href="{a["link"]}">{escape_html(a["title"])}</a>')
            if a["time_ago"]:
                lines.append(f'  {a["time_ago"]}')
            if a["summary"]:
                lines.append(f'  📝 {escape_html(a["summary"])}')

        lines.append(HASHTAGS)
        messages.append("\n".join(lines))

    return messages
