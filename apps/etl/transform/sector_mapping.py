"""
Sector mapping utilities.

Load and apply sector classification to companies.
"""

import pandas as pd
from pathlib import Path
from typing import Optional


def load_sector_mapping(filepath: str = "data/reference/sector_mapping.csv") -> pd.DataFrame:
    """
    Load sector mapping CSV.
    """
    path = Path(filepath)
    
    if not path.exists():
        raise FileNotFoundError(f"Sector mapping file not found: {filepath}")
    
    df = pd.read_csv(path, dtype=str)
    
    required_cols = ['company', 'sector']
    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"Sector mapping missing required column: {col}")
    
    if 'sub_sector' not in df.columns:
        df['sub_sector'] = None
    
    return df


def apply_sector_mapping(companies_df: pd.DataFrame, mapping_df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply sector mapping to companies DataFrame.
    """
    result = companies_df.merge(
        mapping_df[['company', 'sector', 'sub_sector']],
        on='company',
        how='left'
    )
    
    missing_count = result['sector'].isna().sum()
    if missing_count > 0:
        missing_companies = result[result['sector'].isna()]['company'].tolist()
        print(f"⚠️  Warning: {missing_count} companies missing sector mapping:")
        for company in missing_companies[:10]:
            print(f"     - {company}")
        if len(missing_companies) > 10:
            print(f"     ... and {len(missing_companies) - 10} more")
        result['sector'] = result['sector'].fillna('Unknown')
        result['sub_sector'] = result['sub_sector'].fillna('Unknown')
    
    return result
"""
Placeholder files for ETL transform modules
"""
