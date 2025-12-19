"""
Celery tasks for async processing
"""
from celery import Celery
from app.core.config import settings

# Create Celery app
celery_app = Celery(
    "msg2act",
    broker=str(settings.CELERY_BROKER_URL),
    backend=str(settings.CELERY_RESULT_BACKEND),
)

# Configure Celery
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
)

# Import tasks
from .email_tasks import *
from .extraction_tasks import *
