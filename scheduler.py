import schedule
import time
import logging

logger = logging.getLogger(__name__)


def start_scheduler(job_func):
    """Run job_func every hour, forever."""
    schedule.every(1).hours.do(job_func)
    logger.info("⏰ Scheduler started — running every hour")

    while True:
        schedule.run_pending()
        time.sleep(30)  # Check every 30 seconds
