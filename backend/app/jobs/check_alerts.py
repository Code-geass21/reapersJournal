import logging
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.trade import Trade
from app.models.instrument import Instrument
from app.models.price import PriceCache
from app.models.alert import Alert
from app.services import alert_service

logger = logging.getLogger(__name__)

def run():
    """
    Job to compare open trades' SL/TP against the latest price_cache
    and generate alerts if a target is touched.
    """
    db: Session = SessionLocal()
    try:
        # --- BUG 6 FIX: Auto-dismiss lingering SL/TP alerts for trades that are no longer open ---
        lingering_alerts = db.query(Alert).filter(
            Alert.status.in_(['new', 'seen']),
            Alert.kind.in_(['sl_hit', 'tp_hit']),
            ~Alert.trade_id.in_(
                db.query(Trade.id).filter(Trade.status == 'open')
            )
        ).update({"status": "dismissed"}, synchronize_session=False)

        if lingering_alerts > 0:
            logger.info(f"Auto-dismissed {lingering_alerts} lingering alerts for closed trades.")
            db.commit()

        # Fetch open trades that have an active SL or TP
        open_trades = db.query(Trade, Instrument).join(
            Instrument, Trade.instrument_id == Instrument.id
        ).filter(
            Trade.status == 'open',
            (Trade.stop_loss.isnot(None) | Trade.take_profit.isnot(None))
        ).all()

        if not open_trades:
            return

        alerts_created = 0
        for trade, instrument in open_trades:
            cached = db.query(PriceCache).filter(PriceCache.provider_symbol == instrument.provider_symbol).first()
            if not cached or cached.price is None:
                continue

            current = float(cached.price)
            sl = float(trade.stop_loss) if trade.stop_loss else None
            tp = float(trade.take_profit) if trade.take_profit else None

            if trade.direction == 'long':
                if sl and current <= sl:
                    if alert_service.create_alert(db, trade.user_id, 'sl_hit', f"Stop Loss ({sl}) hit for {instrument.symbol} at {current}", trade.id):
                        alerts_created += 1
                elif tp and current >= tp:
                    if alert_service.create_alert(db, trade.user_id, 'tp_hit', f"Take Profit ({tp}) hit for {instrument.symbol} at {current}", trade.id):
                        alerts_created += 1
            elif trade.direction == 'short':
                if sl and current >= sl:
                    if alert_service.create_alert(db, trade.user_id, 'sl_hit', f"Stop Loss ({sl}) hit for {instrument.symbol} at {current}", trade.id):
                        alerts_created += 1
                elif tp and current <= tp:
                    if alert_service.create_alert(db, trade.user_id, 'tp_hit', f"Take Profit ({tp}) hit for {instrument.symbol} at {current}", trade.id):
                        alerts_created += 1

        if alerts_created > 0:
            logger.info(f"Generated {alerts_created} new SL/TP alerts.")

        db.commit()

    except Exception as e:
        db.rollback()
        logger.error(f"Error running check_alerts job: {e}")
        raise e
    finally:
        db.close()
