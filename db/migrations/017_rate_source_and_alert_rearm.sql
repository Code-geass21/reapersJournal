-- Bug 102: remember where each stored FX rate came from
ALTER TABLE trade_executions ADD COLUMN IF NOT EXISTS rate_source VARCHAR(20);

-- Bug 98: price_cache model and table agree (higher precision, price required)
ALTER TABLE price_cache ALTER COLUMN price TYPE NUMERIC(20, 10);
ALTER TABLE price_cache ALTER COLUMN bid   TYPE NUMERIC(20, 10);
ALTER TABLE price_cache ALTER COLUMN ask   TYPE NUMERIC(20, 10);

-- Bug 103: alerts can be retired when price moves back inside the level
ALTER TABLE alerts ADD COLUMN IF NOT EXISTS superseded BOOLEAN NOT NULL DEFAULT FALSE;
