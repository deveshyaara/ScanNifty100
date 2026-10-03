"""
Tests for the warehouse loader normalization helpers.
"""

from __future__ import annotations

import pandas as pd

from apps.etl.load.db_connection import get_db_url
from apps.etl.load.load_dimensions import prepare_dim_company_rows, prepare_dim_year_rows
from apps.etl.load.load_facts import (
    prepare_fact_analysis_rows,
    prepare_fact_documents_rows,
    prepare_fact_pros_cons_rows,
)


def test_get_db_url_prefers_database_url(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://user:pass@localhost:5432/testdb")
    assert get_db_url() == "postgresql://user:pass@localhost:5432/testdb"


def test_prepare_dim_year_rows_handles_booleans():
    frame = pd.DataFrame(
        {
            "year_id": [1, 2],
            "year_label": ["Mar 2024", "TTM"],
            "fiscal_year": [2024, None],
            "sort_order": [20240, 99999],
            "is_ttm": ["False", "True"],
            "is_half_year": ["False", "False"],
        }
    )

    prepared = prepare_dim_year_rows(frame)
    assert bool(prepared.loc[0, "is_ttm"]) is False
    assert bool(prepared.loc[1, "is_ttm"]) is True
    assert list(prepared["year_label"]) == ["Mar 2024", "TTM"]


def test_prepare_dim_company_rows_dedupes_and_renames():
    frame = pd.DataFrame(
        {
            "company": ["TCS", "TCS"],
            "company_name": ["Tata Consultancy Services Ltd", "Duplicate"],
            "sector": ["Information Technology", "Information Technology"],
            "sub_sector": ["IT Services", "IT Services"],
            "company_logo": ["logo1", "logo2"],
            "website": ["https://tcs.com", "https://duplicate.com"],
            "nse_profile": ["nse1", "nse2"],
            "bse_profile": ["bse1", "bse2"],
            "chart_link": ["chart1", "chart2"],
            "about_company": ["about1", "about2"],
            "face_value": [1, 2],
            "book_value": [281, 999],
            "roce_percentage": [64.3, 1.0],
            "roe_percentage": [0.52, 2.0],
        }
    )

    prepared = prepare_dim_company_rows(frame)
    assert len(prepared) == 1
    assert list(prepared.columns)[0] == "symbol"
    assert prepared.iloc[0]["symbol"] == "TCS"
    assert prepared.iloc[0]["nse_url"] == "nse1"


def test_prepare_fact_analysis_rows_filters_unsupported_periods():
    frame = pd.DataFrame(
        {
            "company_id": ["TCS", "TCS", "TCS"],
            "period_label": ["10Y", "1Y", "TTM"],
            "compounded_sales_growth_pct": [11, 12, 13],
            "compounded_profit_growth_pct": [9, 8, 7],
            "stock_price_cagr_pct": [14, 16, 17],
            "return_on_equity_pct": [40, 41, 42],
        }
    )

    prepared = prepare_fact_analysis_rows(frame)
    assert list(prepared["period_label"]) == ["10Y", "1Y", "TTM"]
    assert "roe_pct" in prepared.columns


def test_prepare_fact_pros_cons_rows_uses_company_id_and_skips_blanks():
    frame = pd.DataFrame(
        {
            "company_id": ["HDFCBANK", "", None],
            "is_pro": ["True", "False", "True"],
            "text": ["Good quarter", "Ignored", "Also ignored"],
            "source": ["MANUAL", "MANUAL", "MANUAL"],
        }
    )

    prepared = prepare_fact_pros_cons_rows(frame)
    assert len(prepared) == 1
    assert prepared.iloc[0]["symbol"] == "HDFCBANK"
    assert bool(prepared.iloc[0]["is_pro"]) is True


def test_prepare_fact_documents_rows_uses_company_id_and_year_map():
    frame = pd.DataFrame(
        {
            "company_id": ["ABB", "ABB"],
            "year_label": ["Mar 2024", "Mar 2024"],
            "annual_report": ["https://example.com/a.pdf", "https://example.com/a.pdf"],
        }
    )
    year_mapping = {"Mar 2024": 1}

    prepared = prepare_fact_documents_rows(frame, year_mapping)
    assert len(prepared) == 1
    assert prepared.iloc[0]["symbol"] == "ABB"
    assert int(prepared.iloc[0]["year_id"]) == 1
