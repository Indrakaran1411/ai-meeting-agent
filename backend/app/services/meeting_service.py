"""Service layer handling database operations and business logic for meetings."""

import logging
from datetime import datetime
from typing import Optional
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
