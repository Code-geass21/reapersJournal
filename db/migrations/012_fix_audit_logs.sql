-- FIX FOR BUG 31: Update the global trigger function to log at INFO level
CREATE OR REPLACE FUNCTION log_audit_event()
RETURNS TRIGGER AS $$
DECLARE
    entity_name VARCHAR(50);
    before_data JSONB = NULL;
    after_data JSONB = NULL;
    current_user_id INTEGER;
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

    -- Attempt to read the user_id from a custom Postgres session variable
    BEGIN
        current_user_id := current_setting('app.current_user_id', true)::INTEGER;
    EXCEPTION WHEN OTHERS THEN
        current_user_id := NULL;
    END;

    INSERT INTO app_logs (level, user_id, action, entity_type, entity_id, before, after, source)
    VALUES (
        'INFO', -- Changed from WARNING
        current_user_id,
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
