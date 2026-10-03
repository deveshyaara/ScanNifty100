#!/bin/bash
# Run ScanNifty100 ETL Pipeline

set -e

cd "$(dirname "$0")/.."

echo "=== Running ScanNifty100 ETL Pipeline ==="

source venv/bin/activate

python apps/etl/pipelines/01_extract_n100.py
python apps/etl/pipelines/02_clean_transform.py

echo "=== ETL Pipeline Complete ==="
