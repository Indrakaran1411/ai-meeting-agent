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

# Thread-local event loop cache. Reusing a single loop across sequential Celery tasks
# prevents SQLAlchemy connection pool conflicts. Since SQLAlchemy's AsyncEngine connection pool
# is pinned to the event loop under which it was initialized, generating a new event loop
# for every task execution would cause "Future attached to different loop" errors when
# connections are recycled.
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

    Orchestrates checking out the meeting, triggering TranscriptionService, and logging.
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
            
            meeting, should_continue = await MeetingService.mark_meeting_processing(
                session, meeting_uuid, task_id=task_id_str
            )
            
            if meeting is None:
                logger.warning(
                    "Task: Meeting not found in database (Meeting Not Found). meeting_id=%s, task_id=%s",
                    meeting_uuid,
                    task_id_str,
                )
                return

            if not should_continue:
                logger.info(
                    "Task: Duplicate execution detected (status is already %s). Aborting task. "
                    "meeting_id=%s, task_id=%s, current_status=%s",
                    meeting.status.value,
                    meeting_uuid,
                    task_id_str,
                    meeting.status.value,
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

    # 2. Run TranscriptionService (Executed outside the active database transaction session
    # to avoid holding pool connections open during lengthy CPU-bound audio transcription).
    if file_path:
        logger.info(
            "Task: Initing transcription orchestration. meeting_id=%s, task_id=%s, file_path=%s",
            meeting_uuid,
            task_id_str,
            file_path,
        )

        from app.services.transcription_service import TranscriptionService
        
        try:
            # We run the CPU-heavy, thread-safe Whisper transcription process in the loop's
            # default ThreadPoolExecutor. This prevents blocking the asyncio event loop thread,
            # keeping it responsive to other concurrent tasks (like connection heartbeats).
            loop = asyncio.get_running_loop()
            result = await loop.run_in_executor(
                None,
                TranscriptionService.transcribe_file,
                file_path,
                str(meeting_uuid),
                task_id_str,
            )
        except Exception as stt_err:
            logger.error(
                "Task: Transcription failed (Transcription Failure). Transitioning meeting status to FAILED. meeting_id=%s, task_id=%s. Error: %s",
                meeting_uuid,
                task_id_str,
                str(stt_err),
                exc_info=True,
            )
            # Transition to FAILED inside a separate transaction
            async with async_session_maker() as session:
                try:
                    await MeetingService.mark_meeting_failed(
                        session, meeting_uuid, task_id=task_id_str
                    )
                except Exception as fail_err:
                    logger.critical(
                        "Task: Critical error transitioning meeting status to FAILED. meeting_id=%s, task_id=%s. Error: %s",
                        meeting_uuid,
                        task_id_str,
                        str(fail_err),
                    )
            raise stt_err

        logger.info(
            "Task: Transcription completed successfully. meeting_id=%s, task_id=%s, file_path=%s, "
            "model_size=%s, detected_language=%s, "
            "transcription_time_seconds=%.3f, audio_duration_seconds=%.3f, segment_count=%d",
            meeting_uuid,
            task_id_str,
            file_path,
            settings.WHISPER_MODEL_SIZE,
            result.detected_language,
            result.transcription_duration,
            result.audio_duration,
            len(result.segments),
        )

        # 3. Persist the transcription results inside a single database transaction
        async with async_session_maker() as session:
            try:
                await MeetingService.save_transcript_and_complete(
                    session,
                    meeting_uuid,
                    full_text=result.full_text,
                    audio_duration=result.audio_duration,
                    task_id=task_id_str
                )
            except Exception as persist_err:
                logger.error(
                    "Task: Failed to persist transcript. meeting_id=%s, task_id=%s. Error: %s",
                    meeting_uuid,
                    task_id_str,
                    str(persist_err),
                    exc_info=True,
                )
                raise persist_err

        # 4. Invoke MeetingAnalysisService to analyze the transcript text
        logger.info(
            "Task: Triggering AI analysis layer. meeting_id=%s, task_id=%s",
            meeting_uuid,
            task_id_str,
        )

        from app.services.meeting_analysis_service import MeetingAnalysisService

        try:
            analysis_result = await MeetingAnalysisService.analyze_transcript(
                transcript_text=result.full_text,
                meeting_id=str(meeting_uuid),
                task_id=task_id_str,
            )
            # Log the structured extraction result as required by the verification steps
            logger.info(
                "Task: AI analysis completed. Extracted structured MeetingAnalysis successfully. "
                "meeting_id=%s, task_id=%s, summary_key_points=%d, action_items=%d, decisions=%d, risks=%d, chat_signals=%d, "
                "full_extracted_insights=%s",
                meeting_uuid,
                task_id_str,
                len(analysis_result.summary.key_points),
                len(analysis_result.action_items),
                len(analysis_result.decisions),
                len(analysis_result.risks),
                len(analysis_result.chat_signals),
                analysis_result.model_dump_json(indent=2)
            )
        except Exception as ai_err:
            logger.error(
                "Task: AI analysis failed. meeting_id=%s, task_id=%s. Error: %s",
                meeting_uuid,
                task_id_str,
                str(ai_err),
                exc_info=True,
            )
            raise ai_err

        # 5. Open a fresh database session and persist the AI insights
        logger.info(
            "Task: Persisting extracted AI insights to database. meeting_id=%s, task_id=%s",
            meeting_uuid,
            task_id_str,
        )
        async with async_session_maker() as session:
            try:
                await MeetingService.save_meeting_analysis(
                    db=session,
                    meeting_id=meeting_uuid,
                    analysis=analysis_result,
                    task_id=task_id_str,
                )
            except Exception as db_err:
                logger.error(
                    "Task: Failed to persist AI insights to database. meeting_id=%s, task_id=%s. Error: %s",
                    meeting_uuid,
                    task_id_str,
                    str(db_err),
                    exc_info=True,
                )
                raise db_err



# Celery background task registration configuration:
# - bind=True: Exposes the task instance (self) to dynamically check retries and task IDs.
# - autoretry_for=(Exception,): Retries on any runtime exceptions (e.g. Gemini API quota errors, temp DB drops).
# - retry_backoff=True: Enables exponential delay backoff to prevent thundering herd requests on API recoverability.
# - retry_jitter=True: Randomizes backoff delays slightly to prevent retry synchronization.
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
