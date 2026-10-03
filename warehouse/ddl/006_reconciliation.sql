-- Add real row identity without changing the company-period natural grain.
DO $$
DECLARE t TEXT; natural_columns TEXT;
BEGIN
    FOREACH t IN ARRAY ARRAY['fact_profit_loss','fact_balance_sheet','fact_cash_flow','fact_analysis'] LOOP
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='public' AND table_name=t AND column_name='id') THEN
            natural_columns := CASE WHEN t='fact_analysis' THEN 'symbol, period_label' ELSE 'symbol, year_id' END;
            EXECUTE format('ALTER TABLE %I ADD COLUMN id BIGSERIAL', t);
            EXECUTE format('ALTER TABLE %I ADD CONSTRAINT %I UNIQUE (%s)', t, t || '_natural_key', natural_columns);
            EXECUTE format('ALTER TABLE %I DROP CONSTRAINT %I', t, t || '_pkey');
            EXECUTE format('ALTER TABLE %I ADD PRIMARY KEY (id)', t);
        END IF;
    END LOOP;
END $$;

ALTER TABLE dim_company ALTER COLUMN company_name DROP NOT NULL;
ALTER TABLE dim_company ALTER COLUMN is_active DROP NOT NULL;
ALTER TABLE dim_company ALTER COLUMN is_active DROP DEFAULT;
ALTER TABLE dim_company ADD COLUMN IF NOT EXISTS source VARCHAR(100);
ALTER TABLE dim_company ADD COLUMN IF NOT EXISTS identity_status VARCHAR(40);
ALTER TABLE dim_company ADD COLUMN IF NOT EXISTS profile_available BOOLEAN;

-- Preserve existing values but remove the mathematically invalid FCF expression.
DO $$ BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='fact_cash_flow' AND column_name='free_cash_flow' AND is_generated='ALWAYS') THEN
        ALTER TABLE fact_cash_flow ALTER COLUMN free_cash_flow DROP EXPRESSION;
        UPDATE fact_cash_flow SET free_cash_flow = NULL;
    END IF;
END $$;
ALTER TABLE fact_analysis DROP CONSTRAINT IF EXISTS fact_analysis_period_label_check;
ALTER TABLE fact_analysis ADD CONSTRAINT fact_analysis_period_label_check CHECK (period_label IN ('10Y','5Y','3Y','1Y','TTM'));

CREATE TABLE IF NOT EXISTS dim_industry (
    industry_id BIGSERIAL PRIMARY KEY,
    sector VARCHAR(100) NOT NULL REFERENCES dim_sector(sector_name),
    industry_name VARCHAR(100) NOT NULL,
    UNIQUE(sector, industry_name)
);
CREATE TABLE IF NOT EXISTS dim_date (
    date_id DATE PRIMARY KEY,
    calendar_year INTEGER NOT NULL,
    calendar_month INTEGER NOT NULL CHECK(calendar_month BETWEEN 1 AND 12)
);

CREATE TABLE IF NOT EXISTS fact_metrics (
    id BIGSERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL REFERENCES dim_company(symbol),
    year_id INTEGER NOT NULL REFERENCES dim_year(year_id),
    metrics JSONB NOT NULL,
    overall_score NUMERIC(5,2),
    coverage_pct NUMERIC(5,2) NOT NULL CHECK(coverage_pct BETWEEN 0 AND 100),
    explanation JSONB NOT NULL,
    UNIQUE(symbol, year_id),
    CHECK(overall_score BETWEEN 0 AND 100)
);
CREATE INDEX IF NOT EXISTS idx_metrics_year_score ON fact_metrics(year_id, overall_score DESC);
CREATE TABLE IF NOT EXISTS data_quality_report (
    report_id INTEGER PRIMARY KEY CHECK(report_id=1),
    report JSONB NOT NULL,
    loaded_at TIMESTAMP NOT NULL DEFAULT NOW()
);
ALTER TABLE fact_ml_scores ADD COLUMN IF NOT EXISTS coverage_pct NUMERIC(5,2);
ALTER TABLE fact_ml_scores ADD COLUMN IF NOT EXISTS explanation JSONB;
ALTER TABLE fact_ml_scores ADD COLUMN IF NOT EXISTS year_id INTEGER REFERENCES dim_year(year_id);
ALTER TABLE fact_ml_scores ADD COLUMN IF NOT EXISTS efficiency_score NUMERIC(5,2);
ALTER TABLE fact_ml_scores ADD COLUMN IF NOT EXISTS consistency_score NUMERIC(5,2);
ALTER TABLE fact_ml_scores ALTER COLUMN overall_score DROP NOT NULL;
