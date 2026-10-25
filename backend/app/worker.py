import time
from app.config import settings

if __name__ == "__main__":
    print(f"Worker started. Refresh interval: {settings.price_refresh_secs}s")
    while True:
        # Placeholder for price fetching & alerts
        time.sleep(settings.price_refresh_secs)
