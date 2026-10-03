"""
ETL Utility Functions
====================

Common functions used across ETL scripts:
- Data validation
- Logging helpers
- File operations
- Quality checks
"""

import pandas as pd
import numpy as np
import logging
from pathlib import Path


def setup_logging(script_name, log_dir='data/logs'):
    """
    Setup logging configuration.
    
    Args:
        script_name: Name of the calling script (e.g., '01_extract')
        log_dir: Directory to store log files
    
    Returns:
        Logger instance
    """
    Path(log_dir).mkdir(exist_ok=True)
    
    logger = logging.getLogger(script_name)
    logger.setLevel(logging.DEBUG)
    
    # File handler
    fh = logging.FileHandler(f'{log_dir}/{script_name}.log')
    fh.setLevel(logging.DEBUG)
    
    # Console handler
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    
    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)
    
    logger.addHandler(fh)
    logger.addHandler(ch)
    
    return logger


def safe_divide(numerator, denominator, default=np.nan):
    """
    Safe division that returns NaN instead of Infinity.
    
    Args:
        numerator: Dividend
        denominator: Divisor
        default: Value for undefined operations
    
    Returns:
        Result with NaN for undefined operations
    """
    with np.errstate(divide='ignore', invalid='ignore'):
        result = numerator / denominator
    
    if isinstance(result, pd.Series):
        result = result.where(~np.isinf(result), np.nan)
    else:
        result = np.where(np.isinf(result), np.nan, result)
    
    return result


def validate_null_rate(df, column, max_rate=0.05, logger=None):
    """
    Check that null rate in a column doesn't exceed threshold.
    
    Args:
        df: DataFrame
        column: Column name
        max_rate: Maximum acceptable null rate (default: 5%)
        logger: Logger instance (optional)
    
    Returns:
        Boolean (True if pass, False if fail)
    """
    if column not in df.columns:
        return True
    
    null_rate = df[column].isna().sum() / len(df)
    
    if null_rate > max_rate:
        if logger:
            logger.warning(
                f"⚠️  Column '{column}' has null rate: {null_rate*100:.1f}% "
                f"(threshold: {max_rate*100:.1f}%)"
            )
        return False
    
    return True


def check_infinity_values(df, logger=None):
    """
    Check for Infinity values in numeric columns.
    
    Args:
        df: DataFrame
        logger: Logger instance (optional)
    
    Returns:
        List of (column, count) tuples with Infinity
    """
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    inf_cols = []
    
    for col in numeric_cols:
        inf_count = np.isinf(df[col]).sum()
        if inf_count > 0:
            inf_cols.append((col, inf_count))
            if logger:
                logger.error(f"❌ Column '{col}' has {inf_count} Infinity values")
    
    return inf_cols


def validate_primary_key(df, key_columns, logger=None):
    """
    Check for duplicate primary keys.
    
    Args:
        df: DataFrame
        key_columns: List of column names forming the PK
        logger: Logger instance (optional)
    
    Returns:
        Number of duplicates found
    """
    if not all(col in df.columns for col in key_columns):
        return -1  # Missing column
    
    dups = df.duplicated(subset=key_columns).sum()
    
    if dups > 0 and logger:
        logger.warning(f"⚠️  {dups} duplicate {key_columns} pairs found")
    
    return dups


def validate_referential_integrity(df, fk_column, lookup_df, lookup_column, logger=None):
    """
    Check that all foreign key values exist in lookup table.
    
    Args:
        df: DataFrame with foreign key
        fk_column: Name of FK column
        lookup_df: Lookup table
        lookup_column: Name of column in lookup table
        logger: Logger instance (optional)
    
    Returns:
        Number of orphaned rows
    """
    if fk_column not in df.columns:
        return -1
    
    # Get unique FK values
    fk_values = set(df[fk_column].dropna().unique())
    lookup_values = set(lookup_df[lookup_column].dropna().unique())
    
    orphaned = fk_values - lookup_values
    
    if orphaned and logger:
        logger.warning(
            f"⚠️  {len(orphaned)} unknown {fk_column} values "
            f"(not in {lookup_column})"
        )
        for val in list(orphaned)[:5]:  # Show first 5
            logger.warning(f"    {val}")
    
    return len(orphaned)


def get_data_quality_report(df, name, logger=None):
    """
    Generate a summary data quality report.
    
    Args:
        df: DataFrame
        name: Name for the report
        logger: Logger instance (optional)
    
    Returns:
        Dictionary with quality metrics
    """
    report = {
        'name': name,
        'rows': len(df),
        'columns': len(df.columns),
        'null_rate': (df.isna().sum().sum() / (len(df) * len(df.columns))),
        'has_infinity': np.isinf(df.select_dtypes(include=[np.number])).any().any(),
        'duplicate_rows': df.duplicated().sum(),
        'duplicate_rate': df.duplicated().sum() / len(df),
    }
    
    if logger:
        logger.info(f"\nData Quality Report: {name}")
        logger.info(f"  Rows: {report['rows']}")
        logger.info(f"  Columns: {report['columns']}")
        logger.info(f"  Overall null rate: {report['null_rate']*100:.2f}%")
        logger.info(f"  Has Infinity: {report['has_infinity']}")
        logger.info(f"  Duplicate rows: {report['duplicate_rows']}")
    
    return report


def compare_row_counts(df_before, df_after, name, logger=None):
    """
    Compare row counts before and after transformation.
    
    Args:
        df_before: DataFrame before transformation
        df_after: DataFrame after transformation
        name: Name for the report
        logger: Logger instance (optional)
    
    Returns:
        Dictionary with comparison metrics
    """
    rows_before = len(df_before)
    rows_after = len(df_after)
    rows_removed = rows_before - rows_after
    removal_rate = rows_removed / rows_before * 100 if rows_before > 0 else 0
    
    report = {
        'name': name,
        'rows_before': rows_before,
        'rows_after': rows_after,
        'rows_removed': rows_removed,
        'removal_rate': removal_rate,
    }
    
    if logger:
        logger.info(
            f"{name}: {rows_before} → {rows_after} rows "
            f"({rows_removed} removed, {removal_rate:.1f}%)"
        )
    
    return report


# ============================================================================
# COLUMN NAME STANDARDIZATION
# ============================================================================

def standardize_column_names(df):
    """
    Convert all column names to snake_case.
    
    Examples:
        'Company Name' → 'company_name'
        'OPM %' → 'opm_percent'
        'D&A' → 'dna'
    """
    df.columns = (
        df.columns
        .str.lower()
        .str.replace(' ', '_')
        .str.replace('%', 'percent')
        .str.replace('&', 'and')
        .str.replace('[^a-z0-9_]', '', regex=True)
    )
    return df


def replace_null_variants(df):
    """Replace common null string variants with NaN."""
    null_strings = [
        'NULL', 'Null', 'null',
        'None', 'none',
        '-', '--', '—',
        'N/A', 'NA', 'n/a',
        '#N/A'
    ]
    return df.replace(null_strings, np.nan)


# ============================================================================
# FILE OPERATIONS
# ============================================================================

def ensure_directory(path):
    """Create directory if it doesn't exist."""
    Path(path).mkdir(parents=True, exist_ok=True)


def get_source_files():
    """Get list of source Excel files."""
    source_dir = Path('data/source')
    return {
        'analysis': source_dir / 'analysis.xlsx',
        'balancesheet': source_dir / 'balancesheet.xlsx',
        'cashflow': source_dir / 'cashflow.xlsx',
        'companies': source_dir / 'companies.xlsx',
        'documents': source_dir / 'documents.xlsx',
        'profitandloss': source_dir / 'profitandloss.xlsx',
        'prosandcons': source_dir / 'prosandcons.xlsx',
    }


def verify_source_files(logger=None):
    """
    Verify all source Excel files exist.
    
    Returns:
        Boolean (True if all present, False otherwise)
    """
    files = get_source_files()
    missing = []
    
    for name, path in files.items():
        if not path.exists():
            missing.append(name)
            if logger:
                logger.error(f"❌ Missing: {path}")
    
    if not missing and logger:
        logger.info(f"✅ All 7 source files present")
    
    return len(missing) == 0
