import logging
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert

from app.database import SessionLocal
from app.models.news import NewsEvent
from app.providers import news_forexfactory

logger = logging.getLogger(__name__)

# Memory state to track if we already fetched today
_last_news_date = None

def run():
    """
    Job to fetch upcoming news events and populate the news_events table.
    Now optimized to run only once daily.
    """
    global _last_news_date
    current_date = datetime.now(timezone.utc).date()

    if _last_news_date == current_date:
        return # News already fetched today

    db: Session = SessionLocal()
    try:
        logger.info("Fetching news events via worker...")
        events = news_forexfactory.fetch_upcoming_news()

        if not events:
            logger.info("No upcoming high/medium impact events found.")
            return

        upsert_count = 0
        for event in events:
            # Generate a deterministic UID: time + currency + title
            source_uid = f"{event['time']}_{event['country']}_{event['title']}"

            # Parse ISO string "YYYY-MM-DDTHH:MM:SSZ" to UTC datetime
            dt = datetime.fromisoformat(event['time'].replace('Z', '+00:00'))

            stmt = insert(NewsEvent).values(
                event_time_utc=dt,
                currency=event['country'],
                impact=event['impact'],
                title=event['title'],
                source_uid=source_uid
            )

            # Upsert on conflict
            stmt = stmt.on_conflict_do_update(
                index_elements=['source_uid'],
                set_={
                    'impact': stmt.excluded.impact,
                    'title': stmt.excluded.title
                }
            )
            db.execute(stmt)
            upsert_count += 1

        # Housekeeping: Delete events older than 24 hours
        yesterday = datetime.now(timezone.utc) - timedelta(days=1)
        db.query(NewsEvent).filter(NewsEvent.event_time_utc < yesterday).delete()

        db.commit()

        # Mark as completed for today
        _last_news_date = current_date
        logger.info(f"Successfully upserted {upsert_count} news events.")

    except Exception as e:
        db.rollback()
        logger.error(f"Error running fetch_news job: {e}")
        raise e
    finally:
        db.close()
