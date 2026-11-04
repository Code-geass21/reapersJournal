CREATE TABLE IF NOT EXISTS trade_executions (
    id SERIAL PRIMARY KEY,
    trade_id INTEGER NOT NULL REFERENCES trades(id) ON DELETE CASCADE,
    execution_type VARCHAR(10) NOT NULL, -- 'entry' or 'exit'
    price NUMERIC(15, 5) NOT NULL,
    size NUMERIC(15, 2) NOT NULL, -- lots
    executed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    note TEXT
);

-- We keep the original size/entry_price columns on trades as aggregated caches
-- to avoid rewriting every historical query, but they will now be updated by a trigger/service.
