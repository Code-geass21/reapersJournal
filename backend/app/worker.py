import time
import logging
from app.config import settings
from app.jobs import fetch_prices, fetch_news, check_alerts, scheduled_backup
from app.services import log_service
from app.database import SessionLocal

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

def safe_run(job_func, job_name):
    """FIX FOR BUG 59 & 85: Isolates jobs and logs failures to the DB."""
    try:
        job_func()
    except Exception as e:
        logger.error(f"Job {job_name} failed: {e}")
        # Log to DB so admins can see it in the UI
        db = SessionLocal()
        try:
            log_service.write(
                db=db,
                action=f"worker_job_failed:{job_name}",
                level="ERROR",
                source="worker",
                error_text=str(e)
            )
            db.commit()
        except Exception as log_e:
            logger.error(f"Failed to write worker log to DB: {log_e}")
        finally:
            db.close()

def main():
    interval = settings.price_refresh_secs
    logger.info(f"Worker started. Price refresh interval: {interval} seconds")

    while True:
        logger.info("--- Starting worker cycle ---")
        try:
            # Execute jobs sequentially but isolated
            safe_run(fetch_prices.run, "fetch_prices")
            safe_run(fetch_news.run, "fetch_news")
            safe_run(check_alerts.run, "check_alerts")
            safe_run(scheduled_backup.run, "scheduled_backup")

            logger.info(f"Cycle complete. Sleeping for {interval}s...")
            time.sleep(interval)
        except Exception as e:
            # This catch is just a final safety net for the loop itself
            logger.critical(f"Worker loop encountered a critical error, retrying in 10s: {e}")
            time.sleep(10)

if __name__ == "__main__":
    main()
