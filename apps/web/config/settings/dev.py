"""
Django settings for ScanNifty100 - Development
"""
import os
from pathlib import Path

from .base import *

# Load environment variables from .env
from dotenv import load_dotenv
load_dotenv(BASE_DIR.parents[1] / '.env')

DEBUG = os.environ.get("DJANGO_DEBUG", "True").lower() == "true"
ALLOWED_HOSTS = [
    host.strip()
    for host in os.environ.get("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
    if host.strip()
]

# Database - Use PostgreSQL
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("DB_NAME", "scannifty100"),
        "USER": os.environ.get("DB_USER", "bluestock_user"),
        "PASSWORD": os.environ.get("DB_PASSWORD"),
        "HOST": os.environ.get("DB_HOST", "localhost"),
        "PORT": os.environ.get("DB_PORT", "5433"),
    }
}

# Secret key
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY") or os.environ.get("SECRET_KEY")
if not SECRET_KEY:
    raise ValueError("DJANGO_SECRET_KEY or SECRET_KEY environment variable not set")

# Celery
CELERY_BROKER_URL = os.environ.get("CELERY_BROKER_URL", os.environ.get("REDIS_URL"))
CELERY_RESULT_BACKEND = os.environ.get("CELERY_RESULT_BACKEND", os.environ.get("REDIS_URL"))

# Email
EMAIL_BACKEND = os.environ.get(
    "EMAIL_BACKEND",
    "django.core.mail.backends.console.EmailBackend",
)

# Data paths
RAW_DATA_PATH = os.environ.get("N100_RAW_DIR", "data/raw")
CLEAN_DATA_PATH = os.environ.get("N100_CLEAN_DIR", "data/clean")
STAGING_DATA_PATH = os.environ.get("N100_STAGING_DIR", "data/staging")

# Logging
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
