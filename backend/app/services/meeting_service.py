"""Service layer handling database operations and business logic for meetings."""

import logging
import uuid
from datetime import datetime
from typing import Optional, Tuple
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.meeting import Meeting
from app.models.enums import MeetingStatus

# Setup structured logger
logger = logging.getLogger("app.services.meeting_service")


class MeetingService:
    """Service layer to handle database operations for Meetings."""

    @staticmethod
    async def create_pending_meeting(
        db: AsyncSession,
        *,
        title: str,
        consent_given: bool,
        file_path: str,
        meeting_date: Optional[datetime] = None,
        source: Optional[str] = None,
        duration_minutes: Optional[int] = None,
    ) -> Meeting:
        """
        Creates a new placeholder Meeting record in PENDING status.
        Ensures transaction commits, rollbacks on failure, and structured logging.
        """
        logger.info(
            "Attempting to create pending meeting record: title=%s, source=%s, file_path=%s",
            title,
            source,
            file_path,
        )

        db_meeting = Meeting(
            title=title,
            consent_given=consent_given,
            meeting_date=meeting_date,
            source=source,
            duration_minutes=duration_minutes,
            file_path=file_path,
            status=MeetingStatus.PENDING,
        )

        try:
            db.add(db_meeting)
            await db.commit()
            await db.refresh(db_meeting)
            logger.info(
                "Successfully persisted meeting record to database: id=%s, status=%s",
                db_meeting.id,
                db_meeting.status.value,
            )
            return db_meeting
        except Exception as e:
            await db.rollback()
            logger.error(
                "Failed to commit meeting record to database. Transaction rolled back. Error: %s",
                str(e),
                exc_info=True,
            )
            raise

    @staticmethod
    async def mark_meeting_processing(
        db: AsyncSession, 
        meeting_id: uuid.UUID,
        task_id: Optional[str] = None
    ) -> Tuple[Optional[Meeting], bool]:
        """
        Transitions a meeting from PENDING to PROCESSING status.
        Only commits if the current status is PENDING.
        If already in PROCESSING, COMPLETED, or FAILED, it skips the update.
        Returns a tuple of (Meeting, should_continue) indicating whether processing should continue.
        """
        task_str = task_id or "N/A"
        logger.info(
            "Service: mark_meeting_processing started. meeting_id=%s, task_id=%s",
            meeting_id,
            task_str,
        )
        
        db_meeting = await db.get(Meeting, meeting_id)
        if not db_meeting:
            logger.warning(
                "Service: Meeting not found in database. meeting_id=%s, task_id=%s",
                meeting_id,
                task_str,
            )
            return None, False

        current_status = db_meeting.status
        if current_status != MeetingStatus.PENDING:
            logger.info(
                "Service: Duplicate execution skipped (status is already %s). meeting_id=%s, task_id=%s, current_status=%s",
                current_status.value,
                meeting_id,
                task_str,
                current_status.value,
            )
            return db_meeting, False

        # Perform state transition
        logger.info(
            "Service: Transitioning meeting status from %s to %s. meeting_id=%s, task_id=%s, current_status=%s",
            current_status.value,
            MeetingStatus.PROCESSING.value,
            meeting_id,
            task_str,
            current_status.value,
        )
        db_meeting.status = MeetingStatus.PROCESSING
        
        try:
            await db.commit()
            await db.refresh(db_meeting)
            logger.info(
                "Service: Database commit successful. Status changed to %s. meeting_id=%s, task_id=%s, current_status=%s",
                db_meeting.status.value,
                meeting_id,
                task_str,
                db_meeting.status.value,
            )
            return db_meeting, True
        except Exception as e:
            await db.rollback()
            logger.error(
                "Service: Error committing status change. Transaction rolled back. meeting_id=%s, task_id=%s, current_status=%s. Error: %s",
                meeting_id,
                task_str,
                current_status.value,
                str(e),
                exc_info=True,
            )
            raise e

    @staticmethod
    async def save_transcript_and_complete(
        db: AsyncSession,
        meeting_id: uuid.UUID,
        full_text: str,
        audio_duration: float,
        task_id: Optional[str] = None
    ) -> Optional[Meeting]:
        """
        Saves a single Transcript record for the meeting and updates status to COMPLETED.
        Performs idempotency check by querying for an existing Transcript record.
        Runs within a single transaction with rollback on failure.
        """
        task_str = task_id or "N/A"
        logger.info(
            "Service: save_transcript_and_complete started. meeting_id=%s, task_id=%s",
            meeting_id,
            task_str,
        )

        db_meeting = await db.get(Meeting, meeting_id)
        if not db_meeting:
            logger.warning(
                "Service: Meeting not found in database. meeting_id=%s, task_id=%s",
                meeting_id,
                task_str,
            )
            return None

        # Idempotency check: Query for an existing Transcript record
        from sqlalchemy import select
        from app.models.transcript import Transcript

        stmt = select(Transcript).where(Transcript.meeting_id == meeting_id).limit(1)
        result_set = await db.execute(stmt)
        existing_transcript = result_set.scalar_one_or_none()

        if existing_transcript is not None:
            logger.info(
                "Service: Transcript already exists (Idempotency skip). meeting_id=%s, task_id=%s, current_status=%s",
                meeting_id,
                task_str,
                db_meeting.status.value,
            )
        else:
            logger.info(
                "Service: Creating new Transcript record. meeting_id=%s, task_id=%s",
                meeting_id,
                task_str,
            )
            transcript_record = Transcript(
                meeting_id=meeting_id,
                segment_index=0,
                content=full_text,
                start_time=0.0,
                end_time=audio_duration,
                speaker=None
            )
            db.add(transcript_record)

        # Transition meeting status to COMPLETED
        current_status = db_meeting.status
        logger.info(
            "Service: Transitioning meeting status from %s to COMPLETED. meeting_id=%s, task_id=%s",
            current_status.value,
            meeting_id,
            task_str,
        )
        db_meeting.status = MeetingStatus.COMPLETED

        try:
            await db.commit()
            await db.refresh(db_meeting)
            logger.info(
                "Service: Database commit successful. Meeting status is now COMPLETED. meeting_id=%s, task_id=%s",
                meeting_id,
                task_str,
            )
            return db_meeting
        except Exception as e:
            await db.rollback()
            logger.error(
                "Service: Error saving transcript and completing meeting. Transaction rolled back. meeting_id=%s, task_id=%s. Error: %s",
                meeting_id,
                task_str,
                str(e),
                exc_info=True,
            )
            raise e

    @staticmethod
    async def mark_meeting_failed(
        db: AsyncSession,
        meeting_id: uuid.UUID,
        task_id: Optional[str] = None
    ) -> Optional[Meeting]:
        """
        Transitions a meeting status to FAILED.
        """
        task_str = task_id or "N/A"
        logger.info(
            "Service: mark_meeting_failed started. meeting_id=%s, task_id=%s",
            meeting_id,
            task_str,
        )

        db_meeting = await db.get(Meeting, meeting_id)
        if not db_meeting:
            logger.warning(
                "Service: Meeting not found in database. meeting_id=%s, task_id=%s",
                meeting_id,
                task_str,
            )
            return None

        current_status = db_meeting.status
        logger.info(
            "Service: Transitioning meeting status from %s to FAILED. meeting_id=%s, task_id=%s",
            current_status.value,
            meeting_id,
            task_str,
        )
        db_meeting.status = MeetingStatus.FAILED

        try:
            await db.commit()
            await db.refresh(db_meeting)
            logger.info(
                "Service: Database commit successful. Meeting status is now FAILED. meeting_id=%s, task_id=%s",
                meeting_id,
                task_str,
            )
            return db_meeting
        except Exception as e:
            await db.rollback()
            logger.error(
                "Service: Error transitioning status to FAILED. Transaction rolled back. meeting_id=%s, task_id=%s. Error: %s",
                meeting_id,
                task_str,
                str(e),
                exc_info=True,
            )
            raise e

