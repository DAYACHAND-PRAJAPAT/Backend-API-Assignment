from celery import Celery
from app.config import settings

# Initialize Celery app instance pointing to the auto-loaded Redis broker url
celery_app = Celery(
    "tasks",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL
)

# Auto-discover tasks from the tasks module
celery_app.autodiscover_tasks(['app'])

# Essential configurations for optimal worker execution
celery_app.conf.update(
    task_track_started=True,
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
)