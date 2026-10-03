#!/bin/bash
# Backup ScanNifty100 Database

set -e

BACKUP_DIR="backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/scannifty100_backup_$TIMESTAMP.sql"

mkdir -p "$BACKUP_DIR"

echo "Backing up database to $BACKUP_FILE..."

pg_dump -h localhost -U postgres -d scannifty100_dev > "$BACKUP_FILE"

echo "Backup complete!"
