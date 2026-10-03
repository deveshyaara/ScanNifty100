"""
Analysis table parsing utilities.

Parse multi-period growth strings like "10 Years: 21%" into structured data.
"""

import re
import pandas as pd
from typing import Tuple, Optional


def parse_analysis_string(value: str) -> Tuple[Optional[str], Optional[float]]:
    """
    Parse growth string into period and percentage.
    """
    if pd.isna(value) or value == '':
        return None, None
    raw = str(value).strip()
    # Normalize spacing and remove stray commas
    raw = re.sub(r',', '', raw)
    raw = re.sub(r'\s+', ' ', raw)

    # Pattern: (number) Years: (number)%  OR  TTM: (number)%
    match = re.fullmatch(r'(\d+)\s*Years?\s*:?\s*([\-\+]?\d+(?:\.\d+)?)%?', raw, re.IGNORECASE)
    if match:
        years, pct = match.groups()
        period_label = f"{years}Y"
        value_pct = float(pct)
        return period_label, value_pct

    # Pattern: '1 Year' or 'Last Year' -> treat as 1Y
    match = re.match(r'(?:Last|1)\s*Years?:\s*([\-\+]?\d+(?:\.\d+)?)%?', raw, re.IGNORECASE)
    if match:
        pct = match.group(1)
        return '1Y', float(pct)

    # Check for TTM pattern
    match = re.match(r'TTM:\s*([\-\+]?\d+(?:\.\d+)?)%?', raw, re.IGNORECASE)
    if match:
        pct = match.group(1)
        return 'TTM', float(pct)

    # Fallback
    raise ValueError(f"Could not parse analysis string: {value!r}")


def explode_analysis_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """
    Explode analysis table from wide to long format.
    """
    # Normalize column names
    if 'company_id' in df.columns and 'company' not in df.columns:
        df = df.rename(columns={'company_id': 'company'})
    if 'roe' in df.columns and 'return_on_equity' not in df.columns:
        df = df.rename(columns={'roe': 'return_on_equity'})

    metric_cols = [
        'compounded_sales_growth',
        'compounded_profit_growth',
        'stock_price_cagr',
        'return_on_equity'
    ]
    # Use only those metric columns that exist
    metric_cols = [c for c in metric_cols if c in df.columns]

    parsed_data = []

    for _, row in df.iterrows():
        company = row.get('company')
        if company is None or company == '':
            continue
        periods = {}

        for col in metric_cols:
            cell = row.get(col)
            if pd.notna(cell) and str(cell).strip() != '':
                period, value = parse_analysis_string(cell)
                if period:
                    if period not in periods:
                        periods[period] = {}
                    periods[period][col + '_pct'] = value

        for period, metrics in periods.items():
            parsed_data.append({
                'company': company,
                'period_label': period,
                **metrics
            })

    result = pd.DataFrame(parsed_data)

    # Ensure all metric pct columns exist
    for col in ['compounded_sales_growth', 'compounded_profit_growth', 'stock_price_cagr', 'return_on_equity']:
        col_name = col + '_pct'
        if col_name not in result.columns:
            result[col_name] = pd.NA

    # Reorder columns
    cols = ['company', 'period_label'] + [c + '_pct' for c in ['compounded_sales_growth', 'compounded_profit_growth', 'stock_price_cagr', 'return_on_equity']]
    result = result[cols]

    return result
"""
Placeholder files for ETL transform modules
"""
