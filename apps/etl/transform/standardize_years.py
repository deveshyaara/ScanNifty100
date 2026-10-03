"""
Year standardization utilities.

Converts inconsistent year strings to canonical format with sort order.
"""

import re
import pandas as pd
from typing import Tuple, Optional


def standardize_year(raw_year: str) -> Tuple[Optional[str], Optional[int], Optional[int], bool, bool]:
    """
    Standardize year value to canonical format.
    
    Args:
        raw_year: Raw year string (e.g., 'Mar-24', 'Mar 2024', 'TTM', 'Dec 2012')
        
    Returns:
        Tuple of (year_label, fiscal_year, sort_order, is_ttm, is_half_year)
    """
    if pd.isna(raw_year) or raw_year == '':
        return None, None, None, False, False
    
    raw = str(raw_year).strip()
    
    # Case 1: TTM (Trailing Twelve Months)
    if raw.upper() == 'TTM':
        return 'TTM', None, 99999, True, False
    
    # Case 2: Month-Year format (e.g., "Mar 2024", "Mar-24", "Dec 2012")
    # Pattern: (Month) (optional separator) (2 or 4 digit year)
    match = re.fullmatch(r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[\s\-]?(\d{2}|\d{4})', raw, re.IGNORECASE)
    
    if match:
        month, year = match.groups()
        month = month.capitalize()
        
        # Convert 2-digit year to 4-digit
        year = int(year)
        if year < 100:
            year += 2000 if year < 50 else 1900
        
        year_label = f"{month} {year}"
        
        # Calculate sort_order (year * 10 + month_offset)
        month_offset_map = {
            'Jan': 1, 'Feb': 2, 'Mar': 0,  # Mar is fiscal year end (offset 0)
            'Apr': 1, 'May': 2, 'Jun': 3,
            'Jul': 4, 'Aug': 5, 'Sep': 5,  # Sep is half-year
            'Oct': 6, 'Nov': 7, 'Dec': 2,
        }
        sort_order = year * 10 + month_offset_map.get(month, 0)
        
        # Flag half-year reporting (Sep)
        is_half_year = (month == 'Sep')
        
        return year_label, year, sort_order, False, is_half_year

    # Case 3: Year-only formats like '2013' or '2024.5' (half-year)
    match = re.match(r'^(\d{4})(?:\.(5))?$', raw)
    if match:
        year = int(match.group(1))
        half = bool(match.group(2))
        # Default fiscal label uses Mar for full year, Sep for half-year
        month = 'Sep' if half else 'Mar'
        year_label = f"{month} {year}"
        month_offset_map = {
            'Jan': 1, 'Feb': 2, 'Mar': 0,
            'Apr': 1, 'May': 2, 'Jun': 3,
            'Jul': 4, 'Aug': 5, 'Sep': 5,
            'Oct': 6, 'Nov': 7, 'Dec': 2,
        }
        sort_order = year * 10 + month_offset_map.get(month, 0)
        is_half_year = half
        return year_label, year, sort_order, False, is_half_year
    
    # Fallback: unrecognized format (return as-is with warning)
    return raw, None, None, False, False


def create_year_dimension(df: pd.DataFrame, year_column: str = 'year') -> pd.DataFrame:
    """
    Create standardized year dimension from fact table.
    """
    # Apply standardization
    year_data = df[year_column].apply(standardize_year)
    
    # Unpack tuple results into separate columns
    df['year_label'] = year_data.apply(lambda x: x[0])
    df['fiscal_year'] = year_data.apply(lambda x: x[1])
    df['sort_order'] = year_data.apply(lambda x: x[2])
    df['is_ttm'] = year_data.apply(lambda x: x[3])
    df['is_half_year'] = year_data.apply(lambda x: x[4])
    
    # Drop original raw year column if present
    if year_column in df.columns:
        df = df.drop(columns=[year_column])
    
    return df


def extract_unique_years(dfs: list) -> pd.DataFrame:
    """
    Extract unique year values from multiple DataFrames.
    """
    all_years = []
    
    for df in dfs:
        if 'year_label' in df.columns:
            all_years.extend(df[['year_label', 'fiscal_year', 'sort_order', 'is_ttm', 'is_half_year']].to_dict('records'))
    
    year_dim = pd.DataFrame(all_years)
    if year_dim.empty:
        return pd.DataFrame(columns=['year_id', 'year_label', 'fiscal_year', 'sort_order', 'is_ttm', 'is_half_year'])
    
    year_dim = year_dim.drop_duplicates(subset=['year_label'])
    year_dim = year_dim.sort_values('sort_order')
    year_dim = year_dim.reset_index(drop=True)
    
    year_dim.insert(0, 'year_id', range(1, len(year_dim) + 1))
    
    return year_dim
"""
Placeholder files for ETL transform modules
"""
