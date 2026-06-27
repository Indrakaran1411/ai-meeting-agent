"""API router for meeting upload."""

import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.schemas.meeting import MeetingCreate, MeetingResponseLightweight
from app.services.meeting_service import MeetingService

# Setup structured logger
logger = logging.getLogger("app.api.v1.meetings")

# Initialize FastAPI APIRouter
router = APIRouter(prefix="/meetings", tags=["Meetings"])


@router.post(
    "/upload",
    response_model=MeetingResponseLightweight,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Upload and register a new meeting",
    description="Registers a new meeting in the pipeline. Consent is mandatory.",
)
async def upload_meeting(
    payload: MeetingCreate,
    db: AsyncSession = Depends(get_db),
):
    """
    Endpoint handler to receive meeting details and trigger database persistence.
    Rejects the request with HTTP 400 if consent is not granted.
    """
    if not payload.consent_given:
        logger.warning(
            "Meeting registration rejected: consent_given=False for title=%s",
            payload.title,
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Consent is mandatory to upload and process meeting data.",
        )

    try:
        meeting = await MeetingService.create_pending_meeting(db, payload)
        return MeetingResponseLightweight(
            meeting_id=meeting.id,
            status=meeting.status,
            message="Meeting registered successfully and is pending processing.",
        )
    except Exception as e:
        # Service level logger already logged the traceback, raise general server error
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal database error occurred while registering meeting.",
        )
