-- 1. Create the global trigger function to log row changes
CREATE OR REPLACE FUNCTION log_audit_event()
RETURNS TRIGGER AS $$
DECLARE
    entity_name VARCHAR(50);
    before_data JSONB = NULL;
    after_data JSONB = NULL;
BEGIN
    entity_name := TG_TABLE_NAME;

    IF (TG_OP = 'DELETE') THEN
        before_data := row_to_json(OLD)::jsonb;
    ELSIF (TG_OP = 'UPDATE') THEN
        before_data := row_to_json(OLD)::jsonb;
        after_data := row_to_json(NEW)::jsonb;
    ELSIF (TG_OP = 'INSERT') THEN
        after_data := row_to_json(NEW)::jsonb;
    END IF;

    INSERT INTO app_logs (level, action, entity_type, entity_id, before, after, source)
    VALUES (
        'WARNING',
        'db_trigger.' || LOWER(TG_OP),
        entity_name,
        COALESCE(NEW.id, OLD.id),
        before_data,
        after_data,
        'db_trigger'
    );

    RETURN NULL; -- AFTER trigger
END;
$$ LANGUAGE plpgsql;

-- 2. Attach the audit trigger to the core financial tables
DROP TRIGGER IF EXISTS audit_trades ON trades;
CREATE TRIGGER audit_trades
    AFTER INSERT OR UPDATE OR DELETE ON trades
    FOR EACH ROW EXECUTE FUNCTION log_audit_event();

DROP TRIGGER IF EXISTS audit_strategies ON strategies;
CREATE TRIGGER audit_strategies
    AFTER INSERT OR UPDATE OR DELETE ON strategies
    FOR EACH ROW EXECUTE FUNCTION log_audit_event();

DROP TRIGGER IF EXISTS audit_strategy_rules ON strategy_rules;
CREATE TRIGGER audit_strategy_rules
    AFTER INSERT OR UPDATE OR DELETE ON strategy_rules
    FOR EACH ROW EXECUTE FUNCTION log_audit_event();

DROP TRIGGER IF EXISTS audit_deposits ON strategy_deposits;
CREATE TRIGGER audit_deposits
    AFTER INSERT OR UPDATE OR DELETE ON strategy_deposits
    FOR EACH ROW EXECUTE FUNCTION log_audit_event();


-- 3. Create the v_trade_stats view for lightning fast Dashboards
CREATE OR REPLACE VIEW v_trade_stats AS
SELECT
    user_id,
    strategy_id,
    instrument_id,
    DATE(closed_at) AS close_date,
    COUNT(id) AS trades_count,
    SUM(CASE WHEN pnl_realized > 0 THEN 1 ELSE 0 END) AS winning_trades,
    SUM(CASE WHEN pnl_realized < 0 THEN 1 ELSE 0 END) AS losing_trades,
    SUM(pnl_realized) AS total_pnl,
    SUM(fees) AS total_fees,
    AVG(r_multiple) AS avg_r_multiple
FROM trades
WHERE status = 'closed'
GROUP BY
    user_id, strategy_id, instrument_id, DATE(closed_at);


-- 4. Set up the automated updated_at timestamp trigger
CREATE OR REPLACE FUNCTION update_modified_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

DROP TRIGGER IF EXISTS update_trades_modtime ON trades;
CREATE TRIGGER update_trades_modtime
    BEFORE UPDATE ON trades
    FOR EACH ROW EXECUTE FUNCTION update_modified_column();

DROP TRIGGER IF EXISTS update_strats_modtime ON strategies;
CREATE TRIGGER update_strats_modtime
    BEFORE UPDATE ON strategies
    FOR EACH ROW EXECUTE FUNCTION update_modified_column();
