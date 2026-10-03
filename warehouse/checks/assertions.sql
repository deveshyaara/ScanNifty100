DO $$
BEGIN
    IF EXISTS(SELECT 1 FROM fact_metrics WHERE coverage_pct NOT BETWEEN 0 AND 100 OR overall_score NOT BETWEEN 0 AND 100) THEN
        RAISE EXCEPTION 'Invalid score or coverage';
    END IF;
    IF EXISTS(SELECT 1 FROM fact_cash_flow WHERE free_cash_flow IS NOT NULL) THEN
        RAISE EXCEPTION 'FCF requires capex, which this source does not supply';
    END IF;
    IF EXISTS(SELECT 1 FROM fact_metrics f JOIN dim_company c USING(symbol) WHERE c.identity_status='conflicting_profile' AND f.overall_score IS NOT NULL) THEN
        RAISE EXCEPTION 'Ambiguous identity received a score';
    END IF;
    IF EXISTS(SELECT 1 FROM fact_profit_loss f LEFT JOIN dim_year y USING(year_id) LEFT JOIN dim_company c USING(symbol) WHERE y.year_id IS NULL OR c.symbol IS NULL) THEN
        RAISE EXCEPTION 'Orphaned statement';
    END IF;
END $$;
