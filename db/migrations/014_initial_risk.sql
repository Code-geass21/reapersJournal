-- Adds an immutable record of the original stop loss to preserve accurate R-Multiple tracking
ALTER TABLE trades ADD COLUMN IF NOT EXISTS initial_stop_loss NUMERIC(15, 5);
