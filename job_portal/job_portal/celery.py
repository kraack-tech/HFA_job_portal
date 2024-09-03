import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'job_portal.settings')

# Celery app and configurations from settings.py
app = Celery('job_portal')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks() # Automatically find the tasks