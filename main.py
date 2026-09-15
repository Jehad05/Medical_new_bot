import os
import logging
import telebot
from dotenv import load_dotenv
from fetcher import fetch_all_news, format_message
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
    raise ValueError("❌ BOT_TOKEN or CHAT_ID is missing from .env file!")

bot = telebot.TeleBot(BOT_TOKEN)


def send_news():
    """Fetch news and send to Telegram channel."""
    logger.info("🔄 Fetching news...")
    articles = fetch_all_news()
    message = format_message(articles)

    try:
        bot.send_message(
            chat_id=CHAT_ID,
            text=message,
            parse_mode="Markdown",
            disable_web_page_preview=True
        )
        logger.info("✅ News sent successfully!")
    except Exception as e:
        logger.error(f"❌ Failed to send message: {e}")


if __name__ == "__main__":
    logger.info("🚀 Medical News Bot started!")
    send_news()  # Send immediately on startup
    start_scheduler(send_news)  # Then every hour
