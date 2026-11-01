from sqlalchemy.orm import Session
from app.models.strategy import Strategy, StrategyRule, StrategyDeposit
import logging

logger = logging.getLogger(__name__)

def get_strategy(db: Session, strategy_id: int, user_id: int) -> Strategy:
    return db.query(Strategy).filter(Strategy.id == strategy_id, Strategy.user_id == user_id).first()

def get_strategy_rules(db: Session, strategy_id: int) -> list[StrategyRule]:
    return db.query(StrategyRule).filter(StrategyRule.strategy_id == strategy_id).order_by(StrategyRule.sort_order).all()
