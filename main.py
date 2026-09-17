import os
import logging
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from dotenv import load_dotenv
import requests
from fetcher import fetch_all_news, format_messages
from scheduler import start_scheduler

load_dotenv()
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

if not BOT_TOKEN or not CHAT_ID:
    raise ValueError("❌ BOT_TOKEN or CHAT_ID missing!")


def send_message(text: str):
    """Send a single message to Telegram."""
    try:
        r = requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            json={
                "chat_id": CHAT_ID,
                "text": text,
                "parse_mode": "HTML",
                "disable_web_page_preview": True
            },
            timeout=15,
        )
        r.raise_for_status()
        logger.info("✅ Message sent!")
    except Exception as e:
        logger.error(f"❌ Send failed: {e}")


def send_news():
    """Fetch news and send one message per source."""
    logger.info("🔄 Fetching news...")
    news = fetch_all_news()
    messages = format_messages(news)
    for msg in messages:
        send_message(msg)


class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")
    def log_message(self, *args):
        pass


def run_health_server():
    port = int(os.getenv("PORT", 8080))
    HTTPServer(("0.0.0.0", port), HealthHandler).serve_forever()


if __name__ == "__main__":
    logger.info("🚀 Medical News Bot started!")
    threading.Thread(target=run_health_server, daemon=True).start()
    send_news()
    start_scheduler(send_news)
