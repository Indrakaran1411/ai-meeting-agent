"""Service layer handling database operations and business logic for meetings."""

import logging
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.meeting import Meeting
from app.models.enums import MeetingStatus
from app.schemas.meeting import MeetingCreate

# Setup structured logger
logger = logging.getLogger("app.services.meeting_service")


class MeetingService:
    """Service layer to handle database operations for Meetings."""

    @staticmethod
    async def create_pending_meeting(db: AsyncSession, meeting_in: MeetingCreate) -> Meeting:
        """
        Creates a new placeholder Meeting record in PENDING status.
        Ensures transaction commits, rollbacks on failure, and structured logging.
        """
        logger.info(
            "Attempting to create pending meeting record: title=%s, source=%s",
            meeting_in.title,
            meeting_in.source,
        )

        db_meeting = Meeting(
            title=meeting_in.title,
            consent_given=meeting_in.consent_given,
            meeting_date=meeting_in.meeting_date,
            source=meeting_in.source,
            duration_minutes=meeting_in.duration_minutes,
            file_path=meeting_in.file_path,
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
