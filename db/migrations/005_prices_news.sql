CREATE TABLE IF NOT EXISTS price_cache (
    provider_symbol VARCHAR(50) PRIMARY KEY,
    price NUMERIC(15, 5) NOT NULL,
    bid NUMERIC(15, 5),
    ask NUMERIC(15, 5),
    fetched_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    source VARCHAR(50) DEFAULT 'yfinance'
);

CREATE TABLE IF NOT EXISTS news_events (
    id SERIAL PRIMARY KEY,
    event_time_utc TIMESTAMP WITH TIME ZONE NOT NULL,
    currency VARCHAR(10) NOT NULL,
    impact VARCHAR(20),
    title VARCHAR(255) NOT NULL,
    forecast VARCHAR(50),
    previous VARCHAR(50),
    actual VARCHAR(50),
    source_uid VARCHAR(100) UNIQUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
