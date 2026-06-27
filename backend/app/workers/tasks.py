"""Celery background tasks definitions with retry and logging hardening."""

import asyncio
import logging
import time
import uuid
from typing import Optional

from app.workers.celery_app import celery_app
from app.db.database import async_session_maker
from app.services.meeting_service import MeetingService
from app.core.config import settings

logger = logging.getLogger("app.workers.tasks")

# Thread-local event loop storage to reuse loop across sequential Celery tasks
_loop: Optional[asyncio.AbstractEventLoop] = None


def get_event_loop() -> asyncio.AbstractEventLoop:
    """
    Returns the current event loop or creates a new one.
    Reuses the loop to allow SQLAlchemy's AsyncEngine connection pool
    to remain attached to the same loop, avoiding "Future attached to different loop" errors.
    """
    global _loop
    if _loop is None or _loop.is_closed():
        _loop = asyncio.new_event_loop()
        asyncio.set_event_loop(_loop)
    return _loop


@celery_app.task(name="app.workers.tasks.health_check")
def health_check() -> dict:
    """
    A simple example background task that returns status health check dictionary.
    Used for verifying celery worker execution.
    """
    logger.info("Celery health_check task started execution.")
    return {"status": "healthy"}


async def async_process_meeting(task_id_str: str, meeting_id_str: str) -> None:
    """
    Async coroutine handling the actual database lookup and status transition.
    Integrates detailed structured logging and triggers the TranscriptionService.
    """
    logger.info(
        "Task: Starting async processing coroutine. meeting_id=%s, task_id=%s",
        meeting_id_str,
        task_id_str,
    )
    
    try:
        meeting_uuid = uuid.UUID(meeting_id_str)
    except ValueError as e:
        logger.error(
            "Task: Invalid UUID format received. meeting_id=%s, task_id=%s. Error: %s",
            meeting_id_str,
            task_id_str,
            str(e),
        )
        return

    file_path = None

    # 1. State transition: Mark meeting as PROCESSING in the database
    async with async_session_maker() as session:
        try:
            logger.info(
                "Task: Database session opened. meeting_id=%s, task_id=%s",
                meeting_uuid,
                task_id_str,
            )
            
            meeting = await MeetingService.mark_meeting_processing(
                session, meeting_uuid, task_id=task_id_str
            )
            
            if meeting is None:
                logger.warning(
                    "Task: Meeting not found in database (Meeting Not Found). meeting_id=%s, task_id=%s",
                    meeting_uuid,
                    task_id_str,
                )
                return

            logger.info(
                "Task: Meeting found in database (Meeting Found). meeting_id=%s, task_id=%s, current_status=%s",
                meeting_uuid,
                task_id_str,
                meeting.status.value,
            )
            file_path = meeting.file_path
                
        except Exception as e:
            logger.error(
                "Task: Exception encountered. Executing session rollback. meeting_id=%s, task_id=%s. Error: %s",
                meeting_uuid,
                task_id_str,
                str(e),
                exc_info=True,
            )
            await session.rollback()
            logger.info(
                "Task: Rollback executed. meeting_id=%s, task_id=%s",
                meeting_uuid,
                task_id_str,
            )
            raise e
        finally:
            await session.close()
            logger.info(
                "Task: Closed database session. meeting_id=%s, task_id=%s",
                meeting_uuid,
                task_id_str,
            )

    # 2. Run TranscriptionService (Executed outside the session to free DB pool connection)
    if file_path:
        logger.info(
            "Task: Transcription started. meeting_id=%s, task_id=%s, audio_file=%s, "
            "model_size=%s, device=%s, compute_type=%s",
            meeting_uuid,
            task_id_str,
            file_path,
            settings.WHISPER_MODEL_SIZE,
            settings.WHISPER_DEVICE,
            settings.WHISPER_COMPUTE_TYPE,
        )

        start_time = time.perf_counter()
        
        from app.services.transcription_service import TranscriptionService
        
        # Run transcription CPU-bound work in executor to keep event loop responsive
        loop = asyncio.get_running_loop()
        segments, info = await loop.run_in_executor(
            None,
            TranscriptionService.transcribe_file,
            file_path,
            str(meeting_uuid),
            task_id_str,
        )
        
        transcription_duration = time.perf_counter() - start_time
        audio_duration = getattr(info, "duration", 0.0)
        segment_count = len(segments)

        logger.info(
            "Task: Transcription completed. meeting_id=%s, task_id=%s, audio_file=%s, "
            "model_size=%s, device=%s, compute_type=%s, "
            "transcription_time_seconds=%.3f, audio_duration_seconds=%.3f, segment_count=%d",
            meeting_uuid,
            task_id_str,
            file_path,
            settings.WHISPER_MODEL_SIZE,
            settings.WHISPER_DEVICE,
            settings.WHISPER_COMPUTE_TYPE,
            transcription_duration,
            audio_duration,
            segment_count,
        )


@celery_app.task(
    bind=True,
    name="app.workers.tasks.process_meeting",
    autoretry_for=(Exception,),
    max_retries=settings.CELERY_MAX_RETRIES,
    retry_backoff=settings.CELERY_RETRY_BACKOFF,
    retry_jitter=settings.CELERY_RETRY_JITTER,
)
def process_meeting(self, meeting_id: str) -> None:
    """
    Celery task wrapper to process a meeting background state transition.
    Bridges Celery sync thread to async database coroutine.
    """
    task_id = self.request.id
    logger.info(
        "Task: Received task (Task Started). meeting_id=%s, task_id=%s",
        meeting_id,
        task_id,
    )
    
    try:
        loop = get_event_loop()
        loop.run_until_complete(async_process_meeting(task_id, meeting_id))
        logger.info(
            "Task: Completed task (Task Completed) successfully. meeting_id=%s, task_id=%s",
            meeting_id,
            task_id,
        )
    except Exception as e:
        logger.error(
            "Task: Unexpected exception occurred during task execution. meeting_id=%s, task_id=%s. Error: %s",
            meeting_id,
            task_id,
            str(e),
            exc_info=True,
        )
        raise e
