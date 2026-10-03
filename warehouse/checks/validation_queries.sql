-- ============================================================================
-- ScanNifty100 Warehouse Validation Queries
-- Run these after ETL load to verify dimensional integrity and quality.
-- ============================================================================

SET search_path TO public;

-- Referential integrity: orphaned fact rows should be zero
SELECT 'fact_profit_loss orphans' AS check_name, COUNT(*) AS violation_count
FROM fact_profit_loss f
LEFT JOIN dim_company c ON c.symbol = f.symbol
WHERE c.symbol IS NULL

UNION ALL

SELECT 'fact_balance_sheet orphans', COUNT(*)
FROM fact_balance_sheet f
LEFT JOIN dim_company c ON c.symbol = f.symbol
WHERE c.symbol IS NULL

UNION ALL

SELECT 'fact_cash_flow orphans', COUNT(*)
FROM fact_cash_flow f
LEFT JOIN dim_company c ON c.symbol = f.symbol
WHERE c.symbol IS NULL;

-- Year coverage checks
SELECT
	'companies with fewer than 8 P&L years' AS check_name,
	COUNT(*) AS violation_count
FROM (
	SELECT symbol, COUNT(*) AS year_count
	FROM fact_profit_loss
	GROUP BY symbol
	HAVING COUNT(*) < 8
) sub;

-- Null rates for critical columns
SELECT
	'P&L sales null rate' AS metric,
	ROUND(COUNT(*) FILTER (WHERE sales IS NULL) * 100.0 / NULLIF(COUNT(*), 0), 2) AS null_pct
FROM fact_profit_loss

UNION ALL

SELECT
	'P&L net_profit null rate',
	ROUND(COUNT(*) FILTER (WHERE net_profit IS NULL) * 100.0 / NULLIF(COUNT(*), 0), 2)
FROM fact_profit_loss

UNION ALL

SELECT
	'BS total_assets null rate',
	ROUND(COUNT(*) FILTER (WHERE total_assets IS NULL) * 100.0 / NULLIF(COUNT(*), 0), 2)
FROM fact_balance_sheet;

-- Derived metric sanity checks
SELECT
	'negative debt_to_equity values' AS check_name,
	COUNT(*) AS violation_count
FROM fact_balance_sheet
WHERE debt_to_equity < 0;

SELECT
	'health score range violations' AS check_name,
	COUNT(*) AS violation_count
FROM fact_ml_scores
WHERE overall_score < 0 OR overall_score > 100;

-- Dimension counts summary
SELECT
	(SELECT COUNT(*) FROM dim_sector) AS sectors,
	(SELECT COUNT(*) FROM dim_health_label) AS health_labels,
	(SELECT COUNT(*) FROM dim_year) AS years,
	(SELECT COUNT(*) FROM dim_company) AS companies;
