-- ============================================================================
-- ScanNifty100 Data Warehouse - Indexes and Views
-- Adds performance indexes, materialized views, and analytics views.
-- ============================================================================

SET search_path TO public;

CREATE INDEX IF NOT EXISTS idx_fact_pl_symbol_year ON fact_profit_loss (symbol, year_id);
CREATE INDEX IF NOT EXISTS idx_fact_bs_symbol_year ON fact_balance_sheet (symbol, year_id);
CREATE INDEX IF NOT EXISTS idx_fact_cf_symbol_year ON fact_cash_flow (symbol, year_id);
CREATE INDEX IF NOT EXISTS idx_dim_company_sector_symbol ON dim_company (sector, symbol);
CREATE INDEX IF NOT EXISTS idx_dim_year_fiscal_desc ON dim_year (fiscal_year DESC NULLS LAST);

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_latest_financials AS
WITH latest_year AS (
    SELECT
        pl.symbol,
        MAX(y.sort_order) AS max_sort_order
    FROM fact_profit_loss pl
    JOIN dim_year y ON y.year_id = pl.year_id
    GROUP BY pl.symbol
),
latest_year_rows AS (
    SELECT
        pl.symbol,
        y.year_id,
        y.year_label,
        y.fiscal_year,
        y.sort_order
    FROM fact_profit_loss pl
    JOIN dim_year y ON y.year_id = pl.year_id
    JOIN latest_year ly
      ON ly.symbol = pl.symbol
     AND ly.max_sort_order = y.sort_order
),
latest_scores AS (
    SELECT DISTINCT ON (symbol)
        symbol,
        overall_score,
        profitability_score,
        growth_score,
        leverage_score,
        cashflow_score,
        dividend_score,
        trend_score,
        health_label,
        computed_at
    FROM fact_ml_scores
    ORDER BY symbol, computed_at DESC
)
SELECT
    c.symbol,
    c.company_name,
    c.sector,
    c.sub_sector,
    lyr.year_label AS latest_year,
    lyr.fiscal_year,
    pl.sales,
    pl.expenses,
    pl.operating_profit,
    pl.opm_pct,
    pl.net_profit,
    pl.net_profit_margin_pct,
    pl.eps,
    pl.dividend_payout_pct,
    pl.interest_coverage,
    bs.total_assets,
    bs.borrowings,
    bs.shareholders_equity,
    bs.debt_to_equity,
    bs.equity_ratio,
    cf.operating_activity,
    cf.free_cash_flow,
    ls.overall_score AS health_score,
    ls.health_label,
    ls.profitability_score,
    ls.growth_score,
    ls.leverage_score,
    ls.cashflow_score,
    ls.dividend_score,
    ls.trend_score,
    ls.computed_at AS score_computed_at
FROM dim_company c
LEFT JOIN latest_year_rows lyr ON lyr.symbol = c.symbol
LEFT JOIN fact_profit_loss pl ON pl.symbol = c.symbol AND pl.year_id = lyr.year_id
LEFT JOIN fact_balance_sheet bs ON bs.symbol = c.symbol AND bs.year_id = lyr.year_id
LEFT JOIN fact_cash_flow cf ON cf.symbol = c.symbol AND cf.year_id = lyr.year_id
LEFT JOIN latest_scores ls ON ls.symbol = c.symbol;

CREATE UNIQUE INDEX IF NOT EXISTS idx_mv_latest_financials_symbol ON mv_latest_financials (symbol);
CREATE INDEX IF NOT EXISTS idx_mv_latest_financials_sector ON mv_latest_financials (sector);
CREATE INDEX IF NOT EXISTS idx_mv_latest_financials_health_score ON mv_latest_financials (health_score DESC NULLS LAST);

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_company_timeseries AS
SELECT
    c.symbol,
    c.company_name,
    c.sector,
    y.year_id,
    y.year_label,
    y.fiscal_year,
    y.sort_order,
    pl.sales,
    pl.net_profit,
    pl.opm_pct,
    pl.eps,
    bs.total_assets,
    bs.debt_to_equity,
    cf.free_cash_flow,
    ROUND(
        (
            pl.sales - LAG(pl.sales) OVER (PARTITION BY c.symbol ORDER BY y.sort_order)
        ) * 100.0 / NULLIF(LAG(pl.sales) OVER (PARTITION BY c.symbol ORDER BY y.sort_order), 0),
        2
    ) AS sales_growth_yoy_pct,
    ROUND(
        (
            pl.net_profit - LAG(pl.net_profit) OVER (PARTITION BY c.symbol ORDER BY y.sort_order)
        ) * 100.0 / NULLIF(LAG(pl.net_profit) OVER (PARTITION BY c.symbol ORDER BY y.sort_order), 0),
        2
    ) AS profit_growth_yoy_pct
FROM dim_company c
JOIN fact_profit_loss pl ON pl.symbol = c.symbol
JOIN dim_year y ON y.year_id = pl.year_id
LEFT JOIN fact_balance_sheet bs ON bs.symbol = c.symbol AND bs.year_id = y.year_id
LEFT JOIN fact_cash_flow cf ON cf.symbol = c.symbol AND cf.year_id = y.year_id;

CREATE INDEX IF NOT EXISTS idx_mv_timeseries_symbol ON mv_company_timeseries (symbol);
CREATE INDEX IF NOT EXISTS idx_mv_timeseries_year ON mv_company_timeseries (year_id);

CREATE OR REPLACE VIEW vw_sector_aggregates AS
SELECT
    s.sector_name,
    s.sector_code,
    COUNT(DISTINCT c.symbol) AS company_count,
    ROUND(AVG(mvf.sales), 2) AS avg_sales,
    ROUND(AVG(mvf.net_profit), 2) AS avg_net_profit,
    ROUND(AVG(mvf.opm_pct), 2) AS avg_opm_pct,
    ROUND(AVG(mvf.net_profit_margin_pct), 2) AS avg_net_margin_pct,
    ROUND(AVG(mvf.debt_to_equity), 4) AS avg_debt_to_equity,
    ROUND(AVG(mvf.health_score), 2) AS avg_health_score,
    COUNT(*) FILTER (WHERE mvf.health_label = 'EXCELLENT') AS excellent_count,
    COUNT(*) FILTER (WHERE mvf.health_label = 'GOOD') AS good_count,
    COUNT(*) FILTER (WHERE mvf.health_label IN ('WEAK', 'POOR')) AS weak_poor_count
FROM dim_sector s
LEFT JOIN dim_company c ON c.sector = s.sector_name
LEFT JOIN mv_latest_financials mvf ON mvf.symbol = c.symbol
WHERE s.is_active
GROUP BY s.sector_name, s.sector_code;

CREATE OR REPLACE VIEW vw_data_quality AS
SELECT
    'dim_company' AS entity,
    COUNT(*) AS total_count,
    COUNT(*) FILTER (WHERE sector IS NOT NULL) AS filled_count,
    ROUND(COUNT(*) FILTER (WHERE sector IS NOT NULL) * 100.0 / NULLIF(COUNT(*), 0), 2) AS completeness_pct
FROM dim_company
UNION ALL
SELECT
    'fact_profit_loss' AS entity,
    COUNT(*) AS total_count,
    COUNT(*) FILTER (WHERE sales IS NOT NULL AND net_profit IS NOT NULL) AS filled_count,
    ROUND(COUNT(*) FILTER (WHERE sales IS NOT NULL AND net_profit IS NOT NULL) * 100.0 / NULLIF(COUNT(*), 0), 2)
FROM fact_profit_loss
UNION ALL
SELECT
    'fact_balance_sheet' AS entity,
    COUNT(*) AS total_count,
    COUNT(*) FILTER (WHERE total_assets IS NOT NULL) AS filled_count,
    ROUND(COUNT(*) FILTER (WHERE total_assets IS NOT NULL) * 100.0 / NULLIF(COUNT(*), 0), 2)
FROM fact_balance_sheet
UNION ALL
SELECT
    'fact_cash_flow' AS entity,
    COUNT(*) AS total_count,
    COUNT(*) FILTER (WHERE operating_activity IS NOT NULL) AS filled_count,
    ROUND(COUNT(*) FILTER (WHERE operating_activity IS NOT NULL) * 100.0 / NULLIF(COUNT(*), 0), 2)
FROM fact_cash_flow
UNION ALL
SELECT
    'fact_ml_scores' AS entity,
    COUNT(DISTINCT symbol) AS total_count,
    COUNT(DISTINCT symbol) AS filled_count,
    100.00 AS completeness_pct
FROM fact_ml_scores;

CREATE OR REPLACE FUNCTION refresh_all_materialized_views()
RETURNS TEXT
LANGUAGE plpgsql
AS $$
BEGIN
    REFRESH MATERIALIZED VIEW mv_latest_financials;
    REFRESH MATERIALIZED VIEW mv_company_timeseries;
    RETURN 'All materialized views refreshed at ' || NOW()::TEXT;
END;
$$;

COMMENT ON MATERIALIZED VIEW mv_latest_financials IS 'Latest-year snapshot for dashboards and API consumers';
COMMENT ON MATERIALIZED VIEW mv_company_timeseries IS 'Per-company time series for Power BI and trend charts';
COMMENT ON VIEW vw_sector_aggregates IS 'Sector-level aggregate KPIs';
COMMENT ON VIEW vw_data_quality IS 'Simple warehouse completeness monitoring';

INSERT INTO audit_etl_runs (script_name, run_status, end_time, rows_processed)
VALUES ('004_indexes_views.sql', 'SUCCESS', NOW(), 0)
ON CONFLICT DO NOTHING;
