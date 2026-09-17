
import schedule
import time
import logging

logger = logging.getLogger(__name__)


def start_scheduler(job_func):
    schedule.every(1).hours.do(job_func)
    logger.info("⏰ Scheduler running every hour")
    while True:
        try:
            schedule.run_pending()
        except Exception as e:
            logger.error(f"Scheduler error: {e}")
        time.sleep(30)
