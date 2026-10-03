-- ============================================================================
-- Seed data for dim_sector
-- Sectors mapped from the Nifty 100 company master.
-- ============================================================================

SET search_path TO public;

INSERT INTO dim_sector (sector_name, sector_code, description)
VALUES
    ('Financials', 'FIN', 'Banking, insurance, NBFCs, and other financial services'),
    ('Information Technology', 'IT', 'IT services, software development, and consulting'),
    ('Energy', 'ENRG', 'Power generation, renewables, oil & gas, and utilities'),
    ('Consumer Staples', 'CS', 'FMCG, food, beverages, and household products'),
    ('Consumer Discretionary', 'CD', 'Automobiles, retail, travel, and consumer durables'),
    ('Healthcare', 'HLTH', 'Pharmaceuticals, hospitals, and healthcare services'),
    ('Materials', 'MAT', 'Cement, chemicals, paints, and metals'),
    ('Industrials', 'IND', 'Engineering, capital goods, transport, and defense'),
    ('Telecommunication', 'TEL', 'Telecom operators and related services'),
    ('Real Estate', 'REA', 'Property development and real estate investment')
ON CONFLICT (sector_name) DO UPDATE SET
    sector_code = EXCLUDED.sector_code,
    description = EXCLUDED.description;

INSERT INTO audit_etl_runs (script_name, run_status, end_time, rows_processed)
VALUES ('dim_sector.sql', 'SUCCESS', NOW(), 10)
ON CONFLICT DO NOTHING;