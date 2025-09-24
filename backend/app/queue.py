from celery import Celery
from .config import settings

celery = Celery(
    "reviews", broker=settings.CELERY_BROKER_URL, backend=settings.CELERY_RESULT_BACKEND
)
celery.conf.task_acks_late = True
celery.conf.worker_concurrency = 4
