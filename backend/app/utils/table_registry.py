from app.models.user import User
from app.models.strategy import Strategy, StrategyRule, StrategyDeposit
from app.models.trade import Trade, TradeConditionCheck
from app.models.attachment import Attachment
from app.models.instrument import Market, Instrument

# The master contract for backup and restore.
# Order is strictly topological (parents before children) for safe restoration.
BACKUP_REGISTRY = [
    {
        "name": "users",
        "model": User,
        "user_filter": lambda query, user_id: query.filter(User.id == user_id)
    },
    {
        "name": "markets",
        "model": Market,
        "user_filter": lambda query, user_id: query # Global table, no user filter
    },
    {
        "name": "instruments",
        "model": Instrument,
        "user_filter": lambda query, user_id: query # Global table, no user filter
    },
    {
        "name": "strategies",
        "model": Strategy,
        "user_filter": lambda query, user_id: query.filter(Strategy.user_id == user_id)
    },
    {
        "name": "strategy_rules",
        "model": StrategyRule,
        "user_filter": lambda query, user_id: query.join(Strategy).filter(Strategy.user_id == user_id)
    },
    {
        "name": "strategy_deposits",
        "model": StrategyDeposit,
        "user_filter": lambda query, user_id: query.join(Strategy).filter(Strategy.user_id == user_id)
    },
    {
        "name": "trades",
        "model": Trade,
        "user_filter": lambda query, user_id: query.filter(Trade.user_id == user_id)
    },
    {
        "name": "trade_condition_checks",
        "model": TradeConditionCheck,
        "user_filter": lambda query, user_id: query.join(Trade).filter(Trade.user_id == user_id)
    },
    {
        "name": "attachments",
        "model": Attachment,
        "user_filter": lambda query, user_id: query.filter(Attachment.user_id == user_id)
    }
]
