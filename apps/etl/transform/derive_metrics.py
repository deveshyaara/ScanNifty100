"""
Derived metric computation utilities.

Compute financial ratios and metrics from raw data.
"""

import numpy as np
import pandas as pd


def safe_divide(numerator: pd.Series, denominator: pd.Series, default=np.nan) -> pd.Series:
    """
    Safe division that returns NaN instead of raising errors.
    """
    with np.errstate(divide='ignore', invalid='ignore'):
        result = numerator / denominator
    
    result = result.replace([np.inf, -np.inf], default)
    
    return result


def compute_profit_loss_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute derived metrics for profit & loss statement.
    """
    df = df.copy()
    numeric_cols = ['sales', 'expenses', 'operating_profit', 'net_profit', 'interest']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    df['net_profit_margin_pct'] = safe_divide(df['net_profit'] * 100, df['sales'])
    df['expense_ratio_pct'] = safe_divide(df['expenses'] * 100, df['sales'])
    df['interest_coverage'] = safe_divide(df.get('operating_profit'), df.get('interest'))
    
    return df


def compute_balance_sheet_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute derived metrics for balance sheet.
    """
    df = df.copy()
    numeric_cols = ['equity_capital', 'reserves', 'borrowings', 'total_assets']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    df['shareholders_equity'] = df['equity_capital'] + df['reserves']
    df['debt_to_equity'] = safe_divide(df.get('borrowings'), df['shareholders_equity'])
    df['equity_ratio'] = safe_divide(df['shareholders_equity'], df.get('total_assets'))
    
    return df


def compute_cash_flow_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute derived metrics for cash flow statement.
    """
    df = df.copy()
    numeric_cols = ['operating_activity', 'investing_activity']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # Investing activity includes acquisitions/investments, not only capex.
    df['free_cash_flow'] = np.nan
    
    return df


def compute_cross_table_metrics(pl_df: pd.DataFrame, bs_df: pd.DataFrame, cf_df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute metrics that require joining multiple tables.
    """
    merged = cf_df.merge(
        pl_df[['company', 'year_label', 'net_profit']],
        on=['company', 'year_label'],
        how='left', validate='one_to_one'
    )
    
    merged['cash_conversion_ratio'] = safe_divide(
        merged.get('operating_activity'),
        merged.get('net_profit')
    )
    
    cf_cols = list(cf_df.columns) + ['cash_conversion_ratio']
    return merged[cf_cols]
"""
Placeholder files for ETL transform modules
"""
