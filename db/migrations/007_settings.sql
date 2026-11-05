CREATE TABLE IF NOT EXISTS app_settings (
    key VARCHAR(100) PRIMARY KEY,
    value JSONB NOT NULL,
    description TEXT,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Insert default global settings
INSERT INTO app_settings (key, value, description) VALUES
('maintenance_mode', 'false'::jsonb, 'Locks out all non-admin users if true'),
('allow_registration', 'false'::jsonb, 'Allows new users to register an account'),
('price_provider', '"twelvedata"'::jsonb, 'The active provider for live prices')
ON CONFLICT (key) DO NOTHING;
