"""
Celery configuration for ScanNifty100
"""
import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.dev')

app = Celery('scannifty100')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
