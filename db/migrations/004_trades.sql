CREATE TABLE IF NOT EXISTS trades (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    strategy_id INTEGER NOT NULL REFERENCES strategies(id) ON DELETE CASCADE,
    instrument_id INTEGER NOT NULL REFERENCES instruments(id) ON DELETE RESTRICT,
    direction VARCHAR(10) NOT NULL, -- 'long' or 'short'
    status VARCHAR(20) DEFAULT 'open', -- 'open', 'closed', 'cancelled'
    entry_price NUMERIC(15, 5) NOT NULL,
    size NUMERIC(15, 2) NOT NULL, -- lots
    stop_loss NUMERIC(15, 5),
    take_profit NUMERIC(15, 5),
    opened_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    closed_at TIMESTAMP WITH TIME ZONE,
    exit_price NUMERIC(15, 5),
    fees NUMERIC(15, 2) DEFAULT 0,
    pnl_realized NUMERIC(15, 2),
    r_multiple NUMERIC(10, 2),
    notes TEXT,
    tags TEXT[],
    emotion VARCHAR(50),
    rule_violations JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS trade_condition_checks (
    id SERIAL PRIMARY KEY,
    trade_id INTEGER NOT NULL REFERENCES trades(id) ON DELETE CASCADE,
    rule_id INTEGER NOT NULL REFERENCES strategy_rules(id) ON DELETE CASCADE,
    passed BOOLEAN NOT NULL,
    note TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
