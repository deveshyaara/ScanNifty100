-- ============================================================================
-- ScanNifty100 Data Warehouse - Dimension Tables
-- Creates all conformed dimensions for the star schema.
-- ============================================================================

SET search_path TO public;

CREATE TABLE IF NOT EXISTS dim_sector (
    sector_id SERIAL PRIMARY KEY,
    sector_name VARCHAR(100) NOT NULL UNIQUE,
    sector_code VARCHAR(10) NOT NULL UNIQUE,
    description TEXT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS dim_health_label (
    label_id SERIAL PRIMARY KEY,
    label_name VARCHAR(20) NOT NULL UNIQUE CHECK (label_name IN ('EXCELLENT', 'GOOD', 'AVERAGE', 'WEAK', 'POOR')),
    min_score INTEGER NOT NULL CHECK (min_score >= 0 AND min_score <= 100),
    max_score INTEGER NOT NULL CHECK (max_score >= 0 AND max_score <= 100),
    color_hex CHAR(7) NOT NULL,
    description TEXT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS dim_year (
    year_id SERIAL PRIMARY KEY,
    year_label VARCHAR(20) NOT NULL UNIQUE,
    fiscal_year INTEGER,
    quarter VARCHAR(5),
    is_ttm BOOLEAN NOT NULL DEFAULT FALSE,
    is_half_year BOOLEAN NOT NULL DEFAULT FALSE,
    sort_order INTEGER NOT NULL UNIQUE,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS dim_company (
    symbol VARCHAR(20) PRIMARY KEY,
    company_name VARCHAR(255) NOT NULL,
    sector VARCHAR(100) REFERENCES dim_sector(sector_name) ON UPDATE CASCADE,
    sub_sector VARCHAR(100),
    company_logo TEXT,
    website TEXT,
    nse_url TEXT,
    bse_url TEXT,
    chart_link TEXT,
    about_company TEXT,
    face_value NUMERIC(10,2),
    book_value NUMERIC(10,2),
    roce_pct NUMERIC(8,2),
    roe_pct NUMERIC(8,2),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_dim_sector_name ON dim_sector (sector_name);
CREATE INDEX IF NOT EXISTS idx_dim_sector_code ON dim_sector (sector_code);
CREATE INDEX IF NOT EXISTS idx_dim_company_name ON dim_company (company_name);
CREATE INDEX IF NOT EXISTS idx_dim_company_sector ON dim_company (sector);
CREATE INDEX IF NOT EXISTS idx_dim_company_name_trgm ON dim_company USING gin (company_name gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_dim_year_label ON dim_year (year_label);
CREATE INDEX IF NOT EXISTS idx_dim_year_fiscal_year ON dim_year (fiscal_year);
CREATE INDEX IF NOT EXISTS idx_dim_year_sort_order ON dim_year (sort_order);

DROP TRIGGER IF EXISTS trg_dim_company_updated_at ON dim_company;
CREATE TRIGGER trg_dim_company_updated_at
    BEFORE UPDATE ON dim_company
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS trg_dim_sector_updated_at ON dim_sector;
CREATE TRIGGER trg_dim_sector_updated_at
    BEFORE UPDATE ON dim_sector
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

COMMENT ON TABLE dim_sector IS 'Sector classification dimension';
COMMENT ON TABLE dim_health_label IS 'Health score band definitions';
COMMENT ON TABLE dim_year IS 'Standardized time dimension for fiscal periods';
COMMENT ON TABLE dim_company IS 'Company master dimension';

INSERT INTO audit_etl_runs (script_name, run_status, end_time, rows_processed)
VALUES ('002_dim_tables.sql', 'SUCCESS', NOW(), 0)
ON CONFLICT DO NOTHING;
