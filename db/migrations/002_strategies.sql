CREATE TABLE IF NOT EXISTS strategies (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    market VARCHAR(50) DEFAULT 'FOREX',
    funding_mode VARCHAR(50) DEFAULT 'non_systematic', -- 'systematic' or 'non_systematic'
    sip_amount NUMERIC(15, 2),
    sip_frequency VARCHAR(50),
    start_date DATE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS strategy_rules (
    id SERIAL PRIMARY KEY,
    strategy_id INTEGER NOT NULL REFERENCES strategies(id) ON DELETE CASCADE,
    rule_type VARCHAR(50) NOT NULL, -- 'entry', 'exit', 'risk', 'filter'
    label VARCHAR(255) NOT NULL,
    params JSONB DEFAULT '{}'::jsonb,
    is_required BOOLEAN DEFAULT TRUE,
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS strategy_deposits (
    id SERIAL PRIMARY KEY,
    strategy_id INTEGER NOT NULL REFERENCES strategies(id) ON DELETE CASCADE,
    amount NUMERIC(15, 2) NOT NULL,
    kind VARCHAR(20) NOT NULL, -- 'deposit' or 'withdrawal'
    date DATE NOT NULL,
    note TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
