"""Hourly scheduler with daily maintenance."""
import schedule
import time
import logging

logger = logging.getLogger(__name__)


def start_scheduler(job_func, on_daily=None):
    """Run job_func every hour, forever. Optional daily maintenance."""
    schedule.every(1).hours.do(job_func)

    if on_daily:
        schedule.every().day.at("03:00").do(on_daily)
        logger.info("🧹 Daily cleanup scheduled at 03:00 UTC")

    logger.info("⏰ Scheduler running every hour")

    while True:
        try:
            schedule.run_pending()
        except Exception as e:
            logger.error(f"❌ Scheduler error: {e}")
        time.sleep(30)
