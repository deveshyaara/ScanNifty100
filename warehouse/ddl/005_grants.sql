-- ============================================================================
-- ScanNifty100 Data Warehouse - Permissions
-- Grants required access for the ETL and application user.
-- ============================================================================

SET search_path TO public;

GRANT USAGE ON SCHEMA public TO bluestock_user;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO bluestock_user;
GRANT INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO bluestock_user;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO bluestock_user;
GRANT EXECUTE ON FUNCTION safe_divide(NUMERIC, NUMERIC) TO bluestock_user;
GRANT EXECUTE ON FUNCTION refresh_all_materialized_views() TO bluestock_user;
GRANT EXECUTE ON FUNCTION update_updated_at_column() TO bluestock_user;

ALTER DEFAULT PRIVILEGES IN SCHEMA public
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO bluestock_user;

ALTER DEFAULT PRIVILEGES IN SCHEMA public
GRANT USAGE, SELECT ON SEQUENCES TO bluestock_user;

INSERT INTO audit_etl_runs (script_name, run_status, end_time, rows_processed)
VALUES ('005_grants.sql', 'SUCCESS', NOW(), 0)
ON CONFLICT DO NOTHING;