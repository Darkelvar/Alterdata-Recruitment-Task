from celery import Celery

from app.core.config import settings

broker_url = f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/0"

celery_app = Celery(
    "worker",
    broker=broker_url,
    backend=broker_url,
)

celery_app.autodiscover_tasks(["app.workers.tasks"])
