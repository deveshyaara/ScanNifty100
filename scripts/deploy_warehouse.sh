#!/bin/bash
# Deploy ScanNifty100 warehouse DDL in dependency order.

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"

if [ -f "$ROOT_DIR/.env" ]; then
    set -a
    # shellcheck disable=SC1090
    source "$ROOT_DIR/.env"
    set +a
fi

DB_NAME="${DB_NAME:-scannifty100}"
DB_USER="${DB_USER:-scannifty100}"
DB_PASSWORD="${DB_PASSWORD:-change-me}"
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5433}"

DB_CONN="postgresql://${DB_USER}:${DB_PASSWORD}@${DB_HOST}:${DB_PORT}/${DB_NAME}"

echo "ScanNifty100 Warehouse Deployment"
echo "Target: ${DB_NAME} on ${DB_HOST}:${DB_PORT}"
python -m apps.etl.pipelines.refresh_all --deploy

echo "Warehouse deployment complete"
echo "Validation: psql \"$DB_CONN\" -f warehouse/checks/validation_queries.sql"
