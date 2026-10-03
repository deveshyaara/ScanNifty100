"""
Data quality validation checks for the warehouse loader.
"""

from __future__ import annotations

import logging

from sqlalchemy import text
from sqlalchemy.engine import Engine

logger = logging.getLogger(__name__)


def check_referential_integrity(engine: Engine) -> bool:
    logger.info("\nChecking referential integrity...")
    checks = [
        (
            "Orphaned P&L records",
            """
            SELECT COUNT(*) FROM fact_profit_loss fpl
            WHERE NOT EXISTS (SELECT 1 FROM dim_company c WHERE c.symbol = fpl.symbol)
            """,
        ),
        (
            "Orphaned Balance Sheet records",
            """
            SELECT COUNT(*) FROM fact_balance_sheet fbs
            WHERE NOT EXISTS (SELECT 1 FROM dim_company c WHERE c.symbol = fbs.symbol)
            """,
        ),
        (
            "Orphaned Cash Flow records",
            """
            SELECT COUNT(*) FROM fact_cash_flow fcf
            WHERE NOT EXISTS (SELECT 1 FROM dim_company c WHERE c.symbol = fcf.symbol)
            """,
        ),
        (
            "Orphaned Analysis records",
            """
            SELECT COUNT(*) FROM fact_analysis fa
            WHERE NOT EXISTS (SELECT 1 FROM dim_company c WHERE c.symbol = fa.symbol)
            """,
        ),
        (
            "Orphaned Documents records",
            """
            SELECT COUNT(*) FROM fact_documents fd
            WHERE NOT EXISTS (SELECT 1 FROM dim_company c WHERE c.symbol = fd.symbol)
            """,
        ),
    ]

    passed = True
    with engine.connect() as conn:
        for name, query in checks:
            count = conn.execute(text(query)).scalar() or 0
            if count == 0:
                logger.info("  %s: 0 violations", name)
            else:
                logger.error("  %s: %s violations", name, count)
                passed = False
    return passed


def check_null_rates(engine: Engine) -> bool:
    logger.info("\nChecking null rates...")
    checks = [
        ("P&L sales null rate", "SELECT ROUND(COUNT(*) FILTER (WHERE sales IS NULL) * 100.0 / NULLIF(COUNT(*), 0), 2) FROM fact_profit_loss"),
        ("P&L net_profit null rate", "SELECT ROUND(COUNT(*) FILTER (WHERE net_profit IS NULL) * 100.0 / NULLIF(COUNT(*), 0), 2) FROM fact_profit_loss"),
        ("Balance Sheet total_assets null rate", "SELECT ROUND(COUNT(*) FILTER (WHERE total_assets IS NULL) * 100.0 / NULLIF(COUNT(*), 0), 2) FROM fact_balance_sheet"),
        ("Cash Flow operating_activity null rate", "SELECT ROUND(COUNT(*) FILTER (WHERE operating_activity IS NULL) * 100.0 / NULLIF(COUNT(*), 0), 2) FROM fact_cash_flow"),
    ]

    passed = True
    with engine.connect() as conn:
        for name, query in checks:
            pct = conn.execute(text(query)).scalar() or 0
            if pct < 5.0:
                logger.info("  %s: %s%%", name, pct)
            else:
                logger.warning("  %s: %s%% (threshold: 5%%)", name, pct)
                passed = False
    return passed


def check_data_ranges(engine: Engine) -> bool:
    logger.info("\nChecking data value ranges...")
    checks = [
        ("Negative D/E ratios", "SELECT COUNT(*) FROM fact_balance_sheet WHERE debt_to_equity < 0"),
        ("Negative total assets", "SELECT COUNT(*) FROM fact_balance_sheet WHERE total_assets < 0"),
        ("Sales > 10,00,000 Cr", "SELECT COUNT(*) FROM fact_profit_loss WHERE sales > 1000000"),
        ("Invalid health labels", "SELECT COUNT(*) FROM fact_ml_scores WHERE health_label IS NOT NULL AND health_label NOT IN (SELECT label_name FROM dim_health_label)"),
    ]

    passed = True
    with engine.connect() as conn:
        for name, query in checks:
            count = conn.execute(text(query)).scalar() or 0
            if count == 0:
                logger.info("  %s: 0 violations", name)
            else:
                logger.warning("  %s: %s violations", name, count)
                passed = False
    return passed


def run_all_quality_checks(engine: Engine) -> bool:
    logger.info("\n%s", "=" * 70)
    logger.info("DATA QUALITY CHECKS")
    logger.info("%s", "=" * 70)

    integrity_ok = check_referential_integrity(engine)
    nulls_ok = check_null_rates(engine)
    ranges_ok = check_data_ranges(engine)

    passed = integrity_ok and nulls_ok and ranges_ok
    if passed:
        logger.info("✅ ALL QUALITY CHECKS PASSED")
    else:
        logger.warning("⚠️  SOME QUALITY CHECKS FAILED")
    return passed
"""
Placeholder files for ETL load modules
"""
