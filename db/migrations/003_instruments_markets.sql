CREATE TABLE IF NOT EXISTS markets (
    code VARCHAR(20) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    is_enabled BOOLEAN DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS instruments (
    id SERIAL PRIMARY KEY,
    market_code VARCHAR(20) NOT NULL REFERENCES markets(code) ON DELETE CASCADE,
    symbol VARCHAR(50) NOT NULL,
    provider_symbol VARCHAR(50) NOT NULL,
    pip_size NUMERIC(10, 5) NOT NULL,
    contract_size INTEGER DEFAULT 100000,
    quote_ccy VARCHAR(10) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    UNIQUE(symbol, market_code)
);
