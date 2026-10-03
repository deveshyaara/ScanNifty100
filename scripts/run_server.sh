#!/bin/bash
# Run Django Development Server

set -e

cd "$(dirname "$0")/../apps/web"

source ../../venv/bin/activate

python manage.py runserver 0.0.0.0:8000
