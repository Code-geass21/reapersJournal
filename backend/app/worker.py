import time
import logging
from app.config import settings
from app.jobs import fetch_prices

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

        # Execute jobs
        fetch_prices.run()

        # Sleep until the next cycle
        logger.info(f"Cycle complete. Sleeping for {interval}s...")
        time.sleep(interval)

if __name__ == "__main__":
    main()
