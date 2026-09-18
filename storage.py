"""SQLite storage for deduplication."""
import sqlite3
import logging
from datetime import datetime, timezone, timedelta
from pathlib import Path
from config import DB_PATH, SEEN_RETENTION_DAYS, MAX_ROWS

logger = logging.getLogger(__name__)


def _connect() -> sqlite3.Connection:
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db():
    """Create tables if they don't exist."""
    with _connect() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS seen (
                link TEXT PRIMARY KEY,
                source TEXT,
                title TEXT,
                sent_at TEXT NOT NULL
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_sent_at ON seen(sent_at)")
        conn.commit()
    logger.info(f"🗄️ Database ready at {DB_PATH}")


def is_seen(link: str) -> bool:
    """Check if link was already sent."""
    if not link:
        return False
    with _connect() as conn:
        cur = conn.execute("SELECT 1 FROM seen WHERE link = ?", (link,))
        return cur.fetchone() is not None


def mark_seen(link: str, source: str = "", title: str = ""):
    """Mark link as sent."""
    if not link:
        return
    with _connect() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO seen (link, source, title, sent_at) VALUES (?, ?, ?, ?)",
            (link, source, title, datetime.now(timezone.utc).isoformat())
        )
        conn.commit()


def cleanup_old():
    """Delete entries older than retention period + enforce MAX_ROWS."""
    cutoff = (datetime.now(timezone.utc) - timedelta(days=SEEN_RETENTION_DAYS)).isoformat()
    with _connect() as conn:
        # Delete by age
        cur = conn.execute("DELETE FROM seen WHERE sent_at < ?", (cutoff,))
        deleted_age = cur.rowcount

        # Delete by row count (safety net)
        cur2 = conn.execute("""
            DELETE FROM seen WHERE link IN (
                SELECT link FROM seen
                ORDER BY sent_at ASC
                LIMIT MAX(0, (SELECT COUNT(*) FROM seen) - ?)
            )
        """, (MAX_ROWS,))
        deleted_count = cur2.rowcount

        conn.commit()

    if deleted_age or deleted_count:
        logger.info(f"🧹 Cleanup: {deleted_age} old + {deleted_count} excess removed")


def vacuum():
    """Reclaim disk space after deletions."""
    try:
        with _connect() as conn:
            conn.execute("VACUUM")
        logger.info("🧹 Database vacuumed")
    except Exception as e:
        logger.error(f"❌ Vacuum failed: {e}")


def stats() -> dict:
    """Return quick stats."""
    with _connect() as conn:
        total = conn.execute("SELECT COUNT(*) FROM seen").fetchone()[0]
    return {"total_seen": total}
