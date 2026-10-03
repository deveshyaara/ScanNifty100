#!/usr/bin/env python3
"""
Check if all required source Excel files are present before running ETL.
"""

from __future__ import annotations

from pathlib import Path
import sys

REQUIRED_FILES = [
    "analysis.xlsx",
    "balancesheet.xlsx",
    "cashflow.xlsx",
    "companies.xlsx",
    "documents.xlsx",
    "profitandloss.xlsx",
    "prosandcons.xlsx",
]

def check_source_files(source_dir: Path) -> bool:
    """Check if all required Excel files exist."""
    all_present = True

    print("📂 Checking source files in:", source_dir)
    print("=" * 60)

    for filename in REQUIRED_FILES:
        filepath = source_dir / filename
        if filepath.exists():
            size_mb = filepath.stat().st_size / (1024 * 1024)
            print(f"✅ {filename:25} ({size_mb:.2f} MB)")
        else:
            print(f"❌ {filename:25} MISSING")
            all_present = False

    print("=" * 60)

    if all_present:
        print("✅ All source files present")
        return True
    else:
        print("❌ Some source files are missing")
        print("\nPlease place all Excel files in:", source_dir)
        return False


def main() -> int:
    source_dir = Path("data/source")

    if not source_dir.exists():
        source_dir.mkdir(parents=True, exist_ok=True)
        print(f"📁 Created directory: {source_dir}")

    success = check_source_files(source_dir)
    return 0 if success else 1


if __name__ == "__main__":
    raise SystemExit(main())
