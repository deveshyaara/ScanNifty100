"""
Integration tests for Script 01: Extract from Excel to Raw CSV
=============================================================

Validates that all 7 source Excel files are correctly extracted to CSV.
"""

from __future__ import annotations

import pytest
import pandas as pd
from pathlib import Path
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from apps.etl.pipelines import extract_n100 as extract_module


class TestSourceFilesExist:
    """Test that all required source files are present."""
    
    SOURCE_DIR = Path("n100")
    REQUIRED_FILES = [
        "analysis.xlsx",
        "balancesheet.xlsx",
        "cashflow.xlsx",
        "companies.xlsx",
        "documents.xlsx",
        "profitandloss.xlsx",
        "prosandcons.xlsx",
    ]
    
    @pytest.mark.parametrize("filename", REQUIRED_FILES)
    def test_source_file_exists(self, filename: str):
        """Test that each required source file exists."""
        file_path = self.SOURCE_DIR / filename
        assert file_path.exists(), f"Missing source file: {filename}"
        assert file_path.stat().st_size > 0, f"Empty source file: {filename}"


class TestTitleRowDetection:
    """Test title row detection logic."""
    
    def test_detect_title_row_with_title(self):
        """Test detection when title row is present."""
        # This test assumes at least one file has a title row
        file_path = Path("data/source/analysis.xlsx")
        if file_path.exists():
            result = extract_module.detect_title_row(file_path)
            assert result in [0, 1], "Title row detection should return 0 or 1"
    
    def test_detect_title_row_no_file(self):
        """Test detection handles missing files gracefully."""
        result = extract_module.detect_title_row(Path("nonexistent.xlsx"))
        assert result == 0, "Should return 0 for nonexistent files"


class TestExtractionOutput:
    """Test that extraction produces valid CSV files."""
    
    RAW_DIR = Path("data/raw")
    EXPECTED_FILES = [
        "analysis.csv",
        "balancesheet.csv",
        "cashflow.csv",
        "companies.csv",
        "documents.csv",
        "profitandloss.csv",
        "prosandcons.csv",
    ]
    
    @pytest.mark.parametrize("filename", EXPECTED_FILES)
    def test_raw_file_exists(self, filename: str):
        """Test that each expected CSV file exists after extraction."""
        file_path = self.RAW_DIR / filename
        assert file_path.exists(), f"Missing raw file: {filename}"
        
        # Check file is not empty
        assert file_path.stat().st_size > 0, f"Empty raw file: {filename}"
    
    @pytest.mark.parametrize("filename", EXPECTED_FILES)
    def test_raw_file_loadable(self, filename: str):
        """Test that each CSV can be loaded as DataFrame."""
        file_path = self.RAW_DIR / filename
        if file_path.exists():
            df = pd.read_csv(file_path)
            assert len(df) > 0, f"No data in {filename}"
            assert len(df.columns) > 0, f"No columns in {filename}"


class TestColumnStandardization:
    """Test that column names are properly standardized."""
    RAW_DIR = Path("data/raw")
    
    def test_analysis_columns_snake_case(self):
        """Test analysis.csv has snake_case columns."""
        file_path = self.RAW_DIR / "analysis.csv"
        if file_path.exists():
            df = pd.read_csv(file_path)
            
            # Check no spaces in column names
            for col in df.columns:
                assert ' ' not in col, f"Column '{col}' contains spaces"
                assert col == col.lower(), f"Column '{col}' is not lowercase"
    
    def test_companies_has_company_column(self):
        """Test companies.csv has company column (renamed from id)."""
        file_path = self.RAW_DIR / "companies.csv"
        if file_path.exists():
            df = pd.read_csv(file_path)
            assert 'company' in df.columns, "companies.csv should have 'company' column"


class TestDataQuality:
    """Test basic data quality of extracted files."""
    RAW_DIR = Path("data/raw")
    EXPECTED_FILES = TestExtractionOutput.EXPECTED_FILES
    
    def test_no_duplicate_headers(self):
        """Test that header rows are not duplicated in data."""
        for filename in self.EXPECTED_FILES:
            file_path = self.RAW_DIR / filename
            if file_path.exists():
                df = pd.read_csv(file_path)
                
                if 'company' in df.columns:
                    # Check no row has 'company' as value (header repeat)
                    mask = df['company'].astype(str).str.lower() == 'company'
                    assert not mask.any(), f"Found header repeat in {filename}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
