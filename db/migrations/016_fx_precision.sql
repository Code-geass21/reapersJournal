-- Fix for Bug 89: Increase precision for JPY and other micro-fractional exchange rates
ALTER TABLE trade_executions ALTER COLUMN exchange_rate TYPE NUMERIC(20, 10);
