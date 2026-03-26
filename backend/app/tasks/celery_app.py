"""
Celery application setup.
Workers handle all background agent tasks.
"""
from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "nataprep",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.tasks.scheduled_tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    worker_prefetch_multiplier=1,  # fair scheduling
    task_acks_late=True,           # re-queue on worker crash
    # Beat schedule — periodic tasks
    beat_schedule={
        "daily-update-agent": {
            "task": "app.tasks.scheduled_tasks.run_update_agent",
            "schedule": 86400,  # every 24 hours
        },
        "weekly-syllabus-check": {
            "task": "app.tasks.scheduled_tasks.run_syllabus_agent",
            "schedule": 604800,  # every 7 days
        },
        "monthly-ingestion": {
            "task": "app.tasks.scheduled_tasks.run_ingestion_agent",
            "schedule": 2592000,  # every 30 days
        },
    },
)
