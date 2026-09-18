"""Entry point for the Medical News Bot."""
import os
import time
import logging
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

from dotenv import load_dotenv
import requests

from config import MAX_MESSAGE_LENGTH, SEND_DELAY_SECONDS
from fetcher import fetch_all_news, format_messages
from scheduler import start_scheduler
from storage import init_db, mark_seen, cleanup_old, vacuum, stats

load_dotenv()
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
# Silence urllib3 retry noise
logging.getLogger("urllib3").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

if not BOT_TOKEN or not CHAT_ID:
    raise ValueError("❌ BOT_TOKEN or CHAT_ID missing!")

CHAT_ID = int(CHAT_ID)


# ─── Telegram helpers ───────────────────────────────────
def verify_token():
    """Verify bot token before starting."""
    try:
        r = requests.get(
            f"https://api.telegram.org/bot{BOT_TOKEN}/getMe",
            timeout=10,
        )
        r.raise_for_status()
        data = r.json()["result"]
        logger.info(f"✅ Bot verified: @{data['username']}")
    except Exception as e:
        raise ValueError(f"❌ Invalid BOT_TOKEN: {e}")


def send_message(text: str) -> bool:
    """Send one message, truncating if too long. Returns True on success."""
    if len(text) > MAX_MESSAGE_LENGTH:
        text = text[:MAX_MESSAGE_LENGTH - 3] + "..."
        logger.warning("⚠️ Message truncated")

    try:
        r = requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            json={
                "chat_id": CHAT_ID,
                "text": text,
                "parse_mode": "HTML",
                "disable_web_page_preview": True,
            },
            timeout=15,
        )
        r.raise_for_status()
        return True
    except Exception as e:
        logger.error(f"❌ Send failed: {e}")
        return False


# ─── Main job ───────────────────────────────────────────
def send_news():
    logger.info("🔄 Fetching news...")
    news = fetch_all_news()
    messages = format_messages(news)

    sent_ok = 0
    # ✅ إصلاح: نتتبع المقالات التي أُرسلت فعلاً فقط
    sent_articles: list[tuple[str, dict]] = []

    # قائمة مسطحة: (source, article) بنفس ترتيب messages
    source_articles_flat = [
        (source, article)
        for source, articles in news.items()
        for article in articles
    ]

    for i, (msg, (source, article)) in enumerate(zip(messages, source_articles_flat)):
        if send_message(msg):
            sent_ok += 1
            sent_articles.append((source, article))
        if i < len(messages) - 1:
            time.sleep(SEND_DELAY_SECONDS)

    # ✅ mark_seen فقط للمقالات التي أُرسلت بنجاح
    for source, a in sent_articles:
        mark_seen(a["link"], source, a["title"])

    cleanup_old()
    logger.info(f"✅ Sent {sent_ok}/{len(messages)} messages · {stats()}")


def scheduled_cleanup():
    """Runs daily — cleanup + vacuum."""
    cleanup_old()
    vacuum()


# ─── Health check server ────────────────────────────────
class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/stats":
            db_path = os.getenv("DB_PATH", "/data/seen.db")
            size = os.path.getsize(db_path) if os.path.exists(db_path) else 0
            body = f"DB size: {size} bytes\n{stats()}\n".encode()
        else:
            body = b"OK"

        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):
        pass


def run_health_server():
    port = int(os.getenv("PORT", 8080))
    logger.info(f"🏥 Health server on port {port}")
    HTTPServer(("0.0.0.0", port), HealthHandler).serve_forever()


# ─── Startup ────────────────────────────────────────────
if __name__ == "__main__":
    logger.info("🚀 Medical News Bot starting...")
    verify_token()
    init_db()

    threading.Thread(target=run_health_server, daemon=True).start()

    send_news()
    start_scheduler(send_news, on_daily=scheduled_cleanup)
