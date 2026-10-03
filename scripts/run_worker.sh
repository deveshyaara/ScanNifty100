#!/bin/bash
# Run Celery Worker

set -e

cd "$(dirname "$0")/.."

source venv/bin/activate

celery -A config.celery worker -l info
