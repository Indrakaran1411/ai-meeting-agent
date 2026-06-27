"""Celery application configuration initialization."""

import os
from celery import Celery

# Retrieve Redis connection string from environment variable (broker and backend)
redis_url = os.environ.get("REDIS_URL", "redis://localhost:6379/0")

# Initialize the Celery application
celery_app = Celery(
    "meeting_agent_workers",
    broker=redis_url,
    backend=redis_url,
)

# Apply configuration options matching production hardening constraints
celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    
    # Task reliability settings
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    broker_connection_retry_on_startup=True,
)

# Enable automatic task discovery within the workers package
celery_app.autodiscover_tasks(["app.workers"])
