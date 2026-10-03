"""
Extract module - Read data from source Excel files with title row detection.
"""

from __future__ import annotations

import pandas as pd
from pathlib import Path


def detect_title_row(file_path: str | Path) -> int:
    """
    Detect if Excel file has a title row that should be skipped.
    
    The N100 workbooks have a title row like:
    "Bluestock Fintech  Nifty 100 | Analysis | 20 records"
    
    Returns:
        header_row: 0 if no title row, 1 if title row present
    """
    file_path = Path(file_path)
    df_test = pd.read_excel(file_path, nrows=2, header=None)
    if df_test.empty:
        return 0

    first_cell = str(df_test.iloc[0, 0])
    if any(keyword in first_cell for keyword in ['Bluestock', 'Nifty', 'Fintech']):
        return 1
    
    return 0


def extract_excel_sheet(
    file_path: str | Path,
    sheet_name: str | None = None,
    detect_title: bool = True
) -> pd.DataFrame:
    """
    Extract data from Excel file with automatic title row detection.
    
    Args:
        file_path: Path to Excel file
        sheet_name: Sheet name to extract (None for first sheet)
        detect_title: Whether to auto-detect and skip title rows
    
    Returns:
        DataFrame with the extracted data
    """
    file_path = Path(file_path)
    header_row = detect_title_row(file_path) if detect_title else 0
    
    if sheet_name:
        df = pd.read_excel(file_path, sheet_name=sheet_name, header=header_row)
    else:
        df = pd.read_excel(file_path, header=header_row)
    
    return df


def extract_excel_sheets(file_path: str | Path, sheet_names=None, detect_title: bool = True):
    """
    Extract multiple sheets from Excel file.
    
    Args:
        file_path: Path to Excel file
        sheet_names: List of sheet names to extract (None for all)
        detect_title: Whether to auto-detect and skip title rows
    
    Returns:
        Dictionary of sheet_name -> DataFrame
    """
    file_path = Path(file_path)
    header_row = detect_title_row(file_path) if detect_title else 0
    
    excel_file = pd.ExcelFile(file_path)
    
    if sheet_names is None:
        sheet_names = excel_file.sheet_names
    
    data = {}
    for sheet in sheet_names:
        data[sheet] = pd.read_excel(file_path, sheet_name=sheet, header=header_row)
    
    return data
