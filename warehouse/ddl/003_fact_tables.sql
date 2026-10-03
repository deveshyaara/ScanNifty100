-- ============================================================================
-- ScanNifty100 Data Warehouse - Fact Tables
-- Creates all transactional and analytical fact tables.
-- ============================================================================

SET search_path TO public;

CREATE TABLE IF NOT EXISTS fact_profit_loss (
    symbol VARCHAR(20) NOT NULL REFERENCES dim_company(symbol) ON DELETE CASCADE,
    year_id INTEGER NOT NULL REFERENCES dim_year(year_id) ON DELETE CASCADE,
    sales NUMERIC(20,2),
    expenses NUMERIC(20,2),
    operating_profit NUMERIC(20,2),
    opm_pct NUMERIC(8,2),
    other_income NUMERIC(20,2),
    interest NUMERIC(20,2),
    depreciation NUMERIC(20,2),
    profit_before_tax NUMERIC(20,2),
    tax_pct NUMERIC(8,2),
    net_profit NUMERIC(20,2),
    eps NUMERIC(12,2),
    dividend_payout_pct NUMERIC(8,2),
    net_profit_margin_pct NUMERIC(8,2) GENERATED ALWAYS AS (safe_divide(net_profit * 100, sales)) STORED,
    expense_ratio_pct NUMERIC(8,2) GENERATED ALWAYS AS (safe_divide(expenses * 100, sales)) STORED,
    interest_coverage NUMERIC(10,2) GENERATED ALWAYS AS (safe_divide(operating_profit, interest)) STORED,
    loaded_at TIMESTAMP NOT NULL DEFAULT NOW(),
    PRIMARY KEY (symbol, year_id)
);

CREATE TABLE IF NOT EXISTS fact_balance_sheet (
    symbol VARCHAR(20) NOT NULL REFERENCES dim_company(symbol) ON DELETE CASCADE,
    year_id INTEGER NOT NULL REFERENCES dim_year(year_id) ON DELETE CASCADE,
    equity_capital NUMERIC(20,2),
    reserves NUMERIC(20,2),
    borrowings NUMERIC(20,2),
    other_liabilities NUMERIC(20,2),
    total_liabilities NUMERIC(20,2),
    fixed_assets NUMERIC(20,2),
    cwip NUMERIC(20,2),
    investments NUMERIC(20,2),
    other_assets NUMERIC(20,2),
    total_assets NUMERIC(20,2),
    shareholders_equity NUMERIC(20,2) GENERATED ALWAYS AS (equity_capital + reserves) STORED,
    debt_to_equity NUMERIC(10,4) GENERATED ALWAYS AS (safe_divide(borrowings, equity_capital + reserves)) STORED,
    equity_ratio NUMERIC(10,4) GENERATED ALWAYS AS (safe_divide(equity_capital + reserves, total_assets)) STORED,
    book_value_per_share NUMERIC(12,2),
    loaded_at TIMESTAMP NOT NULL DEFAULT NOW(),
    PRIMARY KEY (symbol, year_id)
);

CREATE TABLE IF NOT EXISTS fact_cash_flow (
    symbol VARCHAR(20) NOT NULL REFERENCES dim_company(symbol) ON DELETE CASCADE,
    year_id INTEGER NOT NULL REFERENCES dim_year(year_id) ON DELETE CASCADE,
    operating_activity NUMERIC(20,2),
    investing_activity NUMERIC(20,2),
    financing_activity NUMERIC(20,2),
    net_cash_flow NUMERIC(20,2),
    free_cash_flow NUMERIC(20,2) GENERATED ALWAYS AS (operating_activity + investing_activity) STORED,
    cash_conversion_ratio NUMERIC(10,4),
    loaded_at TIMESTAMP NOT NULL DEFAULT NOW(),
    PRIMARY KEY (symbol, year_id)
);

CREATE TABLE IF NOT EXISTS fact_analysis (
    symbol VARCHAR(20) NOT NULL REFERENCES dim_company(symbol) ON DELETE CASCADE,
    period_label VARCHAR(10) NOT NULL CHECK (period_label IN ('10Y', '5Y', '3Y', 'TTM')),
    compounded_sales_growth_pct NUMERIC(8,2),
    compounded_profit_growth_pct NUMERIC(8,2),
    stock_price_cagr_pct NUMERIC(8,2),
    roe_pct NUMERIC(8,2),
    loaded_at TIMESTAMP NOT NULL DEFAULT NOW(),
    PRIMARY KEY (symbol, period_label)
);

CREATE TABLE IF NOT EXISTS fact_ml_scores (
    score_id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL REFERENCES dim_company(symbol) ON DELETE CASCADE,
    computed_at TIMESTAMP NOT NULL DEFAULT NOW(),
    overall_score NUMERIC(5,2) NOT NULL CHECK (overall_score >= 0 AND overall_score <= 100),
    profitability_score NUMERIC(5,2) CHECK (profitability_score >= 0 AND profitability_score <= 100),
    growth_score NUMERIC(5,2) CHECK (growth_score >= 0 AND growth_score <= 100),
    leverage_score NUMERIC(5,2) CHECK (leverage_score >= 0 AND leverage_score <= 100),
    cashflow_score NUMERIC(5,2) CHECK (cashflow_score >= 0 AND cashflow_score <= 100),
    dividend_score NUMERIC(5,2) CHECK (dividend_score >= 0 AND dividend_score <= 100),
    trend_score NUMERIC(5,2) CHECK (trend_score >= 0 AND trend_score <= 100),
    health_label VARCHAR(20) REFERENCES dim_health_label(label_name),
    model_version VARCHAR(20),
    UNIQUE (symbol, computed_at)
);

CREATE TABLE IF NOT EXISTS fact_pros_cons (
    insight_id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL REFERENCES dim_company(symbol) ON DELETE CASCADE,
    is_pro BOOLEAN NOT NULL,
    category VARCHAR(100),
    text TEXT NOT NULL,
    source VARCHAR(20) NOT NULL CHECK (source IN ('MANUAL', 'ML')),
    confidence NUMERIC(5,4) CHECK (confidence >= 0 AND confidence <= 1),
    generated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS fact_documents (
    document_id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL REFERENCES dim_company(symbol) ON DELETE CASCADE,
    year_id INTEGER NOT NULL REFERENCES dim_year(year_id) ON DELETE CASCADE,
    document_type VARCHAR(50) NOT NULL DEFAULT 'Annual Report',
    document_url TEXT NOT NULL,
    is_valid_url BOOLEAN DEFAULT TRUE,
    loaded_at TIMESTAMP NOT NULL DEFAULT NOW(),
    UNIQUE (symbol, year_id, document_type)
);

CREATE INDEX IF NOT EXISTS idx_fact_pl_symbol ON fact_profit_loss (symbol);
CREATE INDEX IF NOT EXISTS idx_fact_pl_year_id ON fact_profit_loss (year_id);
CREATE INDEX IF NOT EXISTS idx_fact_bs_symbol ON fact_balance_sheet (symbol);
CREATE INDEX IF NOT EXISTS idx_fact_bs_year_id ON fact_balance_sheet (year_id);
CREATE INDEX IF NOT EXISTS idx_fact_cf_symbol ON fact_cash_flow (symbol);
CREATE INDEX IF NOT EXISTS idx_fact_cf_year_id ON fact_cash_flow (year_id);
CREATE INDEX IF NOT EXISTS idx_fact_analysis_symbol ON fact_analysis (symbol);
CREATE INDEX IF NOT EXISTS idx_fact_ml_scores_symbol ON fact_ml_scores (symbol);
CREATE INDEX IF NOT EXISTS idx_fact_ml_scores_computed_at ON fact_ml_scores (computed_at DESC);
CREATE INDEX IF NOT EXISTS idx_fact_pros_cons_symbol ON fact_pros_cons (symbol);
CREATE INDEX IF NOT EXISTS idx_fact_documents_symbol ON fact_documents (symbol);
CREATE INDEX IF NOT EXISTS idx_fact_documents_year_id ON fact_documents (year_id);

COMMENT ON TABLE fact_profit_loss IS 'Profit and loss fact table';
COMMENT ON TABLE fact_balance_sheet IS 'Balance sheet fact table';
COMMENT ON TABLE fact_cash_flow IS 'Cash flow fact table';
COMMENT ON TABLE fact_analysis IS 'Parsed multi-period growth analysis';
COMMENT ON TABLE fact_ml_scores IS 'ML health score output';
COMMENT ON TABLE fact_pros_cons IS 'Manual and ML-generated insights';
COMMENT ON TABLE fact_documents IS 'Document links and annual report references';

INSERT INTO audit_etl_runs (script_name, run_status, end_time, rows_processed)
VALUES ('003_fact_tables.sql', 'SUCCESS', NOW(), 0)
ON CONFLICT DO NOTHING;
