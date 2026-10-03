"""
Integration tests for Script 02: Clean & Transform
"""

import pytest
from pathlib import Path
import pandas as pd
from apps.etl.transform.standardize_years import standardize_year
from apps.etl.transform.clean_analysis import parse_analysis_string
from apps.etl.transform.derive_metrics import safe_divide

CLEAN_DIR = Path("data/clean")


def test_standardize_year():
    assert standardize_year("Mar 2024") == ("Mar 2024", 2024, 20240, False, False)
    assert standardize_year("Mar-24") == ("Mar 2024", 2024, 20240, False, False)
    assert standardize_year("Sep 2024") == ("Sep 2024", 2024, 20245, False, True)
    assert standardize_year("Dec 2012") == ("Dec 2012", 2012, 20122, False, False)
    assert standardize_year("TTM") == ("TTM", None, 99999, True, False)


def test_parse_analysis_string():
    assert parse_analysis_string("10 Years: 21%") == ("10Y", 21.0)
    assert parse_analysis_string("5 Years: 7%") == ("5Y", 7.0)
    assert parse_analysis_string("3 Years: -2%") == ("3Y", -2.0)
    assert parse_analysis_string("TTM: 15%") == ("TTM", 15.0)


def test_safe_divide():
    import numpy as np
    numerator = pd.Series([10, 20, 30, 40])
    denominator = pd.Series([2, 0, 5, np.nan])
    result = safe_divide(numerator, denominator)
    assert result.iloc[0] == 5.0
    assert pd.isna(result.iloc[1])
    assert result.iloc[2] == 6.0
    assert pd.isna(result.iloc[3])


def test_clean_files_exist():
    expected_files = [
        "analysis.csv",
        "profitandloss.csv",
        "balancesheet.csv",
        "cashflow.csv",
        "companies.csv",
        "documents.csv",
        "prosandcons.csv",
        "dim_year.csv",
    ]
    for filename in expected_files:
        filepath = CLEAN_DIR / filename
        assert filepath.exists(), f"Missing clean file: {filename}"


def test_year_label_standardization():
    fact_files = ["profitandloss.csv", "balancesheet.csv", "cashflow.csv"]
    for filename in fact_files:
        df = pd.read_csv(CLEAN_DIR / filename)
        assert 'year_label' in df.columns
        assert 'year' not in df.columns
        year_labels = df['year_label'].unique()
        for label in year_labels:
            if pd.notna(label):
                assert label == 'TTM' or ' ' in label


def test_derived_metrics_exist():
    pl_df = pd.read_csv(CLEAN_DIR / "profitandloss.csv")
    assert 'net_profit_margin_pct' in pl_df.columns
    assert 'expense_ratio_pct' in pl_df.columns
    assert 'interest_coverage' in pl_df.columns
    bs_df = pd.read_csv(CLEAN_DIR / "balancesheet.csv")
    assert 'shareholders_equity' in bs_df.columns
    assert 'debt_to_equity' in bs_df.columns
    assert 'equity_ratio' in bs_df.columns
    cf_df = pd.read_csv(CLEAN_DIR / "cashflow.csv")
    assert 'free_cash_flow' in cf_df.columns
    assert 'cash_conversion_ratio' in cf_df.columns


def test_sector_mapping_applied():
    df = pd.read_csv(CLEAN_DIR / "companies.csv")
    assert 'sector' in df.columns
    assert 'sub_sector' in df.columns


def test_analysis_exploded():
    df = pd.read_csv(CLEAN_DIR / "analysis.csv")
    assert 'period_label' in df.columns
    assert 'compounded_sales_growth_pct' in df.columns
    assert 'compounded_profit_growth_pct' in df.columns
    periods_per_company = df.groupby('company')['period_label'].count()
    assert periods_per_company.min() >= 1


def test_proscons_split():
    df = pd.read_csv(CLEAN_DIR / "prosandcons.csv")
    assert 'is_pro' in df.columns
    assert 'text' in df.columns
    assert 'source' in df.columns
    assert df['is_pro'].nunique() >= 1
    assert (df['source'] == 'MANUAL').all()


def test_no_infinity_values():
    import numpy as np
    pl_df = pd.read_csv(CLEAN_DIR / "profitandloss.csv")
    bs_df = pd.read_csv(CLEAN_DIR / "balancesheet.csv")
    assert not np.isinf(pl_df['interest_coverage'].dropna()).any()
    assert not np.isinf(bs_df['debt_to_equity'].dropna()).any()
