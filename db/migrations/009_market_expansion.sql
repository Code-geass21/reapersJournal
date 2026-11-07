-- Add derivative-specific columns
ALTER TABLE instruments
ADD COLUMN IF NOT EXISTS expiry DATE,
ADD COLUMN IF NOT EXISTS strike NUMERIC(15, 5),
ADD COLUMN IF NOT EXISTS option_type VARCHAR(4); -- 'CE' or 'PE'

-- Seed and enable the new markets
INSERT INTO markets (code, name, is_enabled) VALUES
('IN_EQUITY', 'Indian Equity', FALSE),
('IN_FUTURES', 'Indian Futures', FALSE),
('IN_OPTIONS', 'Indian Options', FALSE),
('CRYPTO', 'Cryptocurrency', FALSE)
ON CONFLICT (code) DO UPDATE SET is_enabled = FALSE;
