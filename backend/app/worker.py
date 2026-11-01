import time
import logging
from app.config import settings
from app.jobs import fetch_prices, fetch_news
from sqlalchemy.exc import OperationalError

# Configure basic logging for the worker process
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

def main():
    interval = settings.price_refresh_secs
    logger.info(f"Worker started. Price refresh interval: {interval} seconds")

    while True:
        logger.info("--- Starting worker cycle ---")
        try:
            fetch_prices.run()
            # fetch_news.run()  <-- Add this once Step 1 is complete

            logger.info(f"Cycle complete. Sleeping for {interval}s...")
            time.sleep(interval)
        except Exception as e:
            logger.error(f"Worker cycle failed, retrying in 10s: {e}")
            time.sleep(10)
        time.sleep(interval)

if __name__ == "__main__":
    main()
