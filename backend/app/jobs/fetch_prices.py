from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert
import logging

from app.database import SessionLocal
from app.models.trade import Trade
from app.models.instrument import Instrument
from app.models.price import PriceCache
from app.providers import price_twelvedata

logger = logging.getLogger(__name__)

def run():
    """
    Job to fetch current prices for all symbols that have open trades
    and upsert them into the price_cache table.
    """
    db: Session = SessionLocal()
    try:
        open_symbols_query = (
            db.query(Instrument.provider_symbol)
            .join(Trade, Trade.instrument_id == Instrument.id)
            .filter(Trade.status == 'open')
            .distinct()
        )
        symbols = [row[0] for row in open_symbols_query.all()]

        if not symbols:
            logger.info("No open trades found. Skipping price fetch.")
            return

        logger.info(f"Fetching prices for {len(symbols)} symbols using TwelveData...")
        price_data = price_twelvedata.fetch_prices(symbols)

        if not price_data:
            logger.warning("Provider returned no price data.")
            return

        upsert_count = 0
        for symbol, data in price_data.items():
            stmt = insert(PriceCache).values(
                provider_symbol=symbol,
                price=data['price'],
                bid=data.get('bid'),
                ask=data.get('ask'),
                source=data['source']
            )
            stmt = stmt.on_conflict_do_update(
                index_elements=['provider_symbol'],
                set_={
                    'price': stmt.excluded.price,
                    'bid': stmt.excluded.bid,
                    'ask': stmt.excluded.ask,
                    'fetched_at': stmt.excluded.fetched_at,
                    'source': stmt.excluded.source
                }
            )
            db.execute(stmt)
            upsert_count += 1

        db.commit()
        logger.info(f"Successfully upserted {upsert_count} prices into cache.")

    except Exception as e:
        db.rollback()
        logger.error(f"Error running fetch_prices job: {e}")
    finally:
        db.close()
