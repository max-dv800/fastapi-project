import celery

from app.core.config import settings


class BaseTaskWithRetry(celery.Task):
    autoretry_for = (ValueError, KeyError)
    max_retries = 3
    retry_backoff = True
    retry_jitter = False


app_celery = celery.Celery(
    "event_booking", broker=settings.rabbit_url, backend=settings.redis_url
)

app_celery.autodiscover_tasks(packages=["app.tasks"], related_name=None)
