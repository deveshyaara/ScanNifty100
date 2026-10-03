-- ============================================================================
-- ScanNifty100 Data Warehouse - Schema Creation
-- Creates extensions, audit infrastructure, and shared functions.
-- ============================================================================

SET search_path TO public;

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "btree_gin";

CREATE TABLE IF NOT EXISTS audit_etl_runs (
    run_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    script_name VARCHAR(100) NOT NULL,
    run_status VARCHAR(20) NOT NULL CHECK (run_status IN ('RUNNING', 'SUCCESS', 'FAILED')),
    start_time TIMESTAMP NOT NULL DEFAULT NOW(),
    end_time TIMESTAMP,
    rows_processed INTEGER DEFAULT 0,
    error_message TEXT,
    metadata JSONB
);

CREATE INDEX IF NOT EXISTS idx_audit_etl_runs_start_time ON audit_etl_runs (start_time DESC);
CREATE INDEX IF NOT EXISTS idx_audit_etl_runs_status ON audit_etl_runs (run_status);

COMMENT ON TABLE audit_etl_runs IS 'Tracks ETL pipeline executions and row counts';

CREATE OR REPLACE FUNCTION safe_divide(numerator NUMERIC, denominator NUMERIC)
RETURNS NUMERIC
LANGUAGE plpgsql
IMMUTABLE
AS $$
BEGIN
    IF denominator IS NULL OR denominator = 0 THEN
        RETURN NULL;
    END IF;

    RETURN numerator / denominator;
END;
$$;

COMMENT ON FUNCTION safe_divide(NUMERIC, NUMERIC) IS 'Prevents division-by-zero and returns NULL instead';

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$;

COMMENT ON FUNCTION update_updated_at_column() IS 'Maintains updated_at timestamps on mutable dimension tables';

INSERT INTO audit_etl_runs (script_name, run_status, end_time, rows_processed)
VALUES ('001_create_schema.sql', 'SUCCESS', NOW(), 0)
ON CONFLICT DO NOTHING;
