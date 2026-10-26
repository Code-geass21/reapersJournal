-- Insert the Forex market
INSERT INTO markets (code, name, is_enabled)
VALUES ('FOREX', 'Foreign Exchange', TRUE)
ON CONFLICT (code) DO NOTHING;

-- Insert major Forex pairs (Yahoo Finance format for provider_symbol)
INSERT INTO instruments (market_code, symbol, provider_symbol, pip_size, contract_size, quote_ccy) VALUES
('FOREX', 'EUR/USD', 'EURUSD=X', 0.0001, 100000, 'USD'),
('FOREX', 'GBP/USD', 'GBPUSD=X', 0.0001, 100000, 'USD'),
('FOREX', 'USD/JPY', 'USDJPY=X', 0.01, 100000, 'JPY'),
('FOREX', 'USD/CHF', 'USDCHF=X', 0.0001, 100000, 'CHF'),
('FOREX', 'AUD/USD', 'AUDUSD=X', 0.0001, 100000, 'USD'),
('FOREX', 'USD/CAD', 'USDCAD=X', 0.0001, 100000, 'CAD'),
('FOREX', 'NZD/USD', 'NZDUSD=X', 0.0001, 100000, 'USD')
ON CONFLICT (symbol, market_code) DO NOTHING;
