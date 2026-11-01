import time
import logging
from app.config import settings
from app.jobs import fetch_prices, fetch_news

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
            # Execute jobs
            fetch_prices.run()
            fetch_news.run()

            logger.info(f"Cycle complete. Sleeping for {interval}s...")
            time.sleep(interval)
        except Exception as e:
            logger.error(f"Worker cycle failed, retrying in 10s: {e}")
            time.sleep(10)

if __name__ == "__main__":
    main()
