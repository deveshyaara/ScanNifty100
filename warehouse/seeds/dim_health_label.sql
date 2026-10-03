-- ============================================================================
-- Seed data for dim_health_label
-- Health bands used by ML scoring and dashboard formatting.
-- ============================================================================

SET search_path TO public;

INSERT INTO dim_health_label (label_name, min_score, max_score, color_hex, description)
VALUES
    ('EXCELLENT', 85, 100, '#217346', 'Exceptional financial health across all dimensions'),
    ('GOOD', 70, 84, '#70AD47', 'Strong financial health with minor areas for improvement'),
    ('AVERAGE', 50, 69, '#FFD700', 'Moderate financial health with balanced strengths and weaknesses'),
    ('WEAK', 35, 49, '#FF8C00', 'Below-average financial health with notable concerns'),
    ('POOR', 0, 34, '#C0392B', 'Significant financial challenges requiring attention')
ON CONFLICT (label_name) DO UPDATE SET
    min_score = EXCLUDED.min_score,
    max_score = EXCLUDED.max_score,
    color_hex = EXCLUDED.color_hex,
    description = EXCLUDED.description;

INSERT INTO audit_etl_runs (script_name, run_status, end_time, rows_processed)
VALUES ('dim_health_label.sql', 'SUCCESS', NOW(), 5)
ON CONFLICT DO NOTHING;
