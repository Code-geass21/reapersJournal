-- Bug 73: Backfill initial stop loss for pre-014 trades
UPDATE trades SET initial_stop_loss = stop_loss WHERE initial_stop_loss IS NULL;

-- Bug 72: Add exchange rate tracking to lock historical P&L
ALTER TABLE trade_executions ADD COLUMN IF NOT EXISTS exchange_rate NUMERIC(15, 5);
