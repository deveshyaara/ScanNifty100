CREATE OR REPLACE VIEW vw_metrics AS
SELECT f.id, f.symbol, f.year_id, f.overall_score, f.coverage_pct,
       m.*, f.explanation::text AS score_explanation
FROM fact_metrics f
CROSS JOIN LATERAL jsonb_to_record(f.metrics) AS m(
    sales numeric, net_profit numeric, eps numeric, operating_profit numeric,
    ebit numeric, ebitda numeric, revenue_growth_pct numeric, profit_growth_pct numeric,
    eps_growth_pct numeric, revenue_cagr_3y_pct numeric, revenue_cagr_5y_pct numeric,
    profit_cagr_3y_pct numeric, profit_cagr_5y_pct numeric,
    net_profit_margin_pct numeric, operating_margin_pct numeric, ebit_margin_pct numeric,
    ebitda_margin_pct numeric, roe_pct numeric, roa_pct numeric, roce_pct numeric,
    debt_to_equity numeric, equity_ratio numeric, asset_turnover numeric,
    cash_conversion_ratio numeric, cfo_margin_pct numeric, operating_activity numeric,
    investing_activity numeric, financing_activity numeric,
    total_assets numeric, total_liabilities numeric, shareholders_equity numeric,
    borrowings numeric, equity_growth_pct numeric, asset_growth_pct numeric,
    statement_coverage_pct numeric, free_cash_flow numeric, capex numeric,
    cash numeric, net_debt numeric, current_ratio numeric, quick_ratio numeric,
    profit_positive_fraction numeric, cfo_positive_fraction numeric,
    profitability_score numeric, growth_score numeric, balance_sheet_score numeric,
    cash_flow_score numeric, efficiency_score numeric, consistency_score numeric,
    status text, health_label text, model_version text, identity_status text
);

CREATE OR REPLACE VIEW vw_latest_metrics AS
SELECT DISTINCT ON(m.symbol) m.*
FROM vw_metrics m JOIN dim_year y USING(year_id)
ORDER BY m.symbol,y.sort_order DESC;

CREATE OR REPLACE VIEW vw_company_coverage AS
SELECT c.symbol,c.identity_status,c.profile_available,
    EXISTS(SELECT 1 FROM fact_profit_loss f WHERE f.symbol=c.symbol) AS has_profit_loss,
    EXISTS(SELECT 1 FROM fact_balance_sheet f WHERE f.symbol=c.symbol) AS has_balance_sheet,
    EXISTS(SELECT 1 FROM fact_cash_flow f WHERE f.symbol=c.symbol) AS has_cash_flow,
    EXISTS(SELECT 1 FROM fact_documents f WHERE f.symbol=c.symbol) AS has_documents,
    EXISTS(SELECT 1 FROM fact_analysis f WHERE f.symbol=c.symbol) AS has_source_analysis,
    EXISTS(SELECT 1 FROM fact_pros_cons f WHERE f.symbol=c.symbol) AS has_source_insights
FROM dim_company c;

CREATE OR REPLACE VIEW vw_score_contributions AS
SELECT f.id::text || ':' || metric.key AS contribution_id,f.symbol,f.year_id,
    metric.key AS metric_name,metric.value->>'component' AS component,
    (metric.value->>'value')::numeric AS metric_value,
    (metric.value->>'score')::numeric AS metric_score,
    (metric.value->>'weight')::numeric AS metric_weight,
    metric.value->>'status' AS availability
FROM fact_metrics f CROSS JOIN LATERAL jsonb_each(f.explanation->'contributions') metric;
