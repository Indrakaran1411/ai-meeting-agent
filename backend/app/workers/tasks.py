"""Celery background tasks definitions."""

import logging
from app.workers.celery_app import celery_app

logger = logging.getLogger("app.workers.tasks")


@celery_app.task(name="app.workers.tasks.health_check")
def health_check() -> dict:
    """
    A simple example background task that returns status health check dictionary.
    Used for verifying celery worker execution.
    """
    logger.info("Celery health_check task started execution.")
    return {"status": "healthy"}
