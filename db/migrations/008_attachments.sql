CREATE TABLE IF NOT EXISTS attachments (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    owner_type VARCHAR(50) NOT NULL, -- 'trade' or 'avatar'
    owner_id INTEGER NOT NULL,
    path VARCHAR(255) NOT NULL,
    mime VARCHAR(100),
    size INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
