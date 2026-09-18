"""Fetch and format medical news from RSS feeds."""
import re
import time
import logging
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

import feedparser
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from config import (
    SOURCES, MAX_ARTICLES_PER_SOURCE, MAX_ARTICLE_AGE_HOURS,
    TIMEOUTS, DEFAULT_TIMEOUT, RETRY_TOTAL, RETRY_BACKOFF, RETRY_STATUS,
    HASHTAGS,
)
from storage import is_seen

logger = logging.getLogger(__name__)


# ─── HTTP Session with retry ────────────────────────────
_session = requests.Session()
_retry = Retry(
    total=RETRY_TOTAL,
    backoff_factor=RETRY_BACKOFF,
    status_forcelist=RETRY_STATUS,
    allowed_methods=["GET"],
)
_session.mount("https://", HTTPAdapter(max_retries=_retry))
_session.mount("http://", HTTPAdapter(max_retries=_retry))


# ─── Helpers ────────────────────────────────────────────
def clean_html(text: str) -> str:
    return re.sub(r"<[^>]+>", "", text or "").strip()


def escape_html(text: str) -> str:
    return (text.replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;"))


def parse_published(entry) -> datetime | None:
    """Parse entry date, normalize to UTC."""
    published = entry.get("published", "") or entry.get("updated", "")
    if not published:
        return None
    try:
        parsed = parsedate_to_datetime(published)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed
    except Exception:
        return None


def time_ago(published: datetime | None) -> str:
    """Human-readable time since publication."""
    if not published:
        return ""
    now = datetime.now(timezone.utc)
    diff = now - published
    seconds = diff.total_seconds()

    if seconds < 0:
        return "🕐 just now"

    minutes = int(seconds / 60)
    if minutes < 60:
        return f"🕐 {minutes}m ago"
    elif minutes < 1440:
        return f"🕐 {minutes // 60}h ago"
    else:
        return f"🕐 {minutes // 1440}d ago"


# ─── Fetching ───────────────────────────────────────────
def fetch_feed(name: str, url: str) -> list[dict]:
    """Fetch one RSS source with retry and deduplication."""
    timeout = TIMEOUTS.get(name, DEFAULT_TIMEOUT)
    t0 = time.time()

    try:
        r = _session.get(
            url,
            timeout=timeout,
            headers={"User-Agent": "MedicalNewsBot/1.0"},
        )
        r.raise_for_status()
        feed = feedparser.parse(r.content)

        articles = []
        skipped_seen = 0
        skipped_old = 0

        for entry in getattr(feed, "entries", []):
            if len(articles) >= MAX_ARTICLES_PER_SOURCE:
                break

            link = entry.get("link", "")
            if not link:
                continue

            # Deduplication
            if is_seen(link):
                skipped_seen += 1
                continue

            # Age filter
            published = parse_published(entry)
            if published:
                age_hours = (datetime.now(timezone.utc) - published).total_seconds() / 3600
                if age_hours > MAX_ARTICLE_AGE_HOURS:
                    skipped_old += 1
                    continue

            # Summary
            summary = clean_html(entry.get("summary", ""))
            if len(summary) > 200:
                summary = summary[:200].rsplit(" ", 1)[0] + "..."

            articles.append({
                "source": name,
                "title": clean_html(entry.get("title", "No title")),
                "link": link,
                "summary": summary,
                "time_ago": time_ago(published),
                "timestamp": published.timestamp() if published else 0,
            })

        elapsed = time.time() - t0
        logger.info(
            f"✅ {name}: {len(articles)} new "
            f"(skipped: {skipped_seen} seen, {skipped_old} old) "
            f"in {elapsed:.2f}s"
        )
        return articles

    except Exception as e:
        elapsed = time.time() - t0
        logger.error(f"❌ {name}: {e} (after {elapsed:.2f}s)")
        return []


def fetch_all_news() -> dict[str, list[dict]]:
    """Return dict of source -> articles, sorted by freshness."""
    result = {}
    for name, url in SOURCES.items():
        articles = fetch_feed(name, url)
        if articles:
            # Sort by timestamp descending (newest first)
            articles.sort(key=lambda a: a["timestamp"], reverse=True)
            result[name] = articles

    # ✅ إصلاح الباغ الأصلي: result.values() وليس result.items()
    total = sum(len(v) for v in result.values())
    logger.info(f"📰 Total: {total} new articles from {len(result)} sources")
    return result


# ─── Formatting ─────────────────────────────────────────
def format_messages(news: dict[str, list[dict]]) -> list[str]:
    """Return one message per source."""
    if not news:
        return ["⚠️ No new medical news at this time."]

    messages = []

    for source, articles in news.items():
        lines = [
            "🏥 <b>Medical News Update</b>",
            f"📊 {len(articles)} new · {source}",
            "━━━━━━━━━━━━━━━━━━━━",
        ]

        for i, a in enumerate(articles, 1):
            num = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣"][i - 1] if i <= 5 else f"{i}."
            lines.append(f'\n{num} <a href="{a["link"]}">{escape_html(a["title"])}</a>')
            if a["time_ago"]:
                lines.append(f'   {a["time_ago"]}')
            if a["summary"]:
                lines.append(f'   📝 {escape_html(a["summary"])}')

        lines.append(HASHTAGS)
        messages.append("\n".join(lines))

    return messages
