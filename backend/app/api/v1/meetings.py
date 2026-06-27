"""API router for meeting upload."""

import logging
import os
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Form, File, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

import uuid
from typing import Optional, List
from app.db.database import get_db
from app.schemas.meeting import (
    MeetingResponseLightweight,
    MeetingDetailResponse,
    MeetingSummaryResponse,
    ActionItemResponse,
    DecisionResponse,
    RiskResponse
)
from app.services.meeting_service import MeetingService
from app.services.storage_service import StorageService
from app.workers.tasks import process_meeting

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
    title: str = Form(..., description="The title of the meeting"),
    consent_given: bool = Form(..., description="Mandatory consent flag confirming recording and processing permission"),
    meeting_date: Optional[datetime] = Form(None, description="The timestamp when the meeting occurred"),
    source: Optional[str] = Form(None, description="Origin platform, e.g. Zoom, Teams, Upload"),
    duration_minutes: Optional[int] = Form(None, description="Duration of the meeting in minutes"),
    audio_file: UploadFile = File(..., description="Audio file of the meeting (MP3, WAV, or MP4/M4A)"),
    db: AsyncSession = Depends(get_db),
):
    """
    Endpoint handler to receive meeting details and files.
    Rejects the request with HTTP 400 if consent is not granted.
    """
    if not consent_given:
        logger.warning(
            "Meeting registration rejected: consent_given=False for title=%s",
            title,
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Consent is mandatory to upload and process meeting data.",
        )

    # 1. Save audio file using StorageService
    file_path = await StorageService.save_audio_file(audio_file)

    # 2. Persist the meeting record via MeetingService
    try:
        meeting = await MeetingService.create_pending_meeting(
            db,
            title=title,
            consent_given=consent_given,
            file_path=file_path,
            meeting_date=meeting_date,
            source=source,
            duration_minutes=duration_minutes,
        )
        # Enqueue Celery background processing task
        try:
            process_meeting.delay(str(meeting.id))
            logger.info("API: Successfully enqueued Celery processing task for meeting ID: %s", meeting.id)
        except Exception as queue_err:
            logger.error("API: Failed to enqueue Celery task for meeting ID: %s. Error: %s", meeting.id, queue_err)

        return MeetingResponseLightweight(
            meeting_id=meeting.id,
            status=meeting.status,
            message="Meeting registered successfully and is pending processing.",
        )
    except Exception:
        # Delete file if database persistence fails to avoid orphaned files on disk
        if os.path.exists(file_path):
            try:
                os.unlink(file_path)
                logger.info(
                    "Deleted orphaned file %s after database transaction failure",
                    file_path,
                )
            except Exception as cleanup_err:
                logger.error(
                    "Failed to delete orphaned file %s: %s",
                    file_path,
                    str(cleanup_err),
                )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal database error occurred while registering meeting.",
        )


@router.get(
    "/{meeting_id}",
    response_model=MeetingDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Get full details of a specific meeting",
    description="Retrieves a meeting's metadata, processing status, and summary description.",
)
async def get_meeting(
    meeting_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Endpoint handler to fetch meeting metadata and state.
    """
    logger.info("API: Fetching meeting details. meeting_id=%s", meeting_id)
    meeting = await MeetingService.get_meeting_by_id(db, meeting_id)
    if not meeting:
        logger.warning("API: Meeting not found. meeting_id=%s", meeting_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Meeting with ID {meeting_id} not found.",
        )
    return meeting


@router.get(
    "/{meeting_id}/summary",
    response_model=MeetingSummaryResponse,
    status_code=status.HTTP_200_OK,
    summary="Get summary of a specific meeting",
    description="Retrieves only the AI-generated high-level summary paragraph for a meeting.",
)
async def get_meeting_summary(
    meeting_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Endpoint handler to fetch meeting summary text.
    """
    logger.info("API: Fetching meeting summary. meeting_id=%s", meeting_id)
    meeting = await MeetingService.get_meeting_by_id(db, meeting_id)
    if not meeting:
        logger.warning("API: Meeting not found. meeting_id=%s", meeting_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Meeting with ID {meeting_id} not found.",
        )
    return MeetingSummaryResponse(meeting_id=meeting.id, summary=meeting.summary)


@router.get(
    "/{meeting_id}/action-items",
    response_model=List[ActionItemResponse],
    status_code=status.HTTP_200_OK,
    summary="Get action items of a specific meeting",
    description="Retrieves all AI-extracted action items associated with a meeting.",
)
async def get_meeting_action_items(
    meeting_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Endpoint handler to fetch action items list.
    """
    logger.info("API: Fetching meeting action items. meeting_id=%s", meeting_id)
    meeting = await MeetingService.get_meeting_by_id(db, meeting_id)
    if not meeting:
        logger.warning("API: Meeting not found. meeting_id=%s", meeting_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Meeting with ID {meeting_id} not found.",
        )
    action_items = meeting.action_items
    logger.info("API: Returning action items. meeting_id=%s, count=%d", meeting_id, len(action_items))
    return action_items


@router.get(
    "/{meeting_id}/decisions",
    response_model=List[DecisionResponse],
    status_code=status.HTTP_200_OK,
    summary="Get decisions of a specific meeting",
    description="Retrieves all AI-extracted decisions associated with a meeting.",
)
async def get_meeting_decisions(
    meeting_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Endpoint handler to fetch decisions list.
    """
    logger.info("API: Fetching meeting decisions. meeting_id=%s", meeting_id)
    meeting = await MeetingService.get_meeting_by_id(db, meeting_id)
    if not meeting:
        logger.warning("API: Meeting not found. meeting_id=%s", meeting_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Meeting with ID {meeting_id} not found.",
        )
    decisions = meeting.decisions
    logger.info("API: Returning decisions. meeting_id=%s, count=%d", meeting_id, len(decisions))
    return decisions


@router.get(
    "/{meeting_id}/risks",
    response_model=List[RiskResponse],
    status_code=status.HTTP_200_OK,
    summary="Get risks of a specific meeting",
    description="Retrieves all AI-extracted risks associated with a meeting.",
)
async def get_meeting_risks(
    meeting_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Endpoint handler to fetch risks list.
    """
    logger.info("API: Fetching meeting risks. meeting_id=%s", meeting_id)
    meeting = await MeetingService.get_meeting_by_id(db, meeting_id)
    if not meeting:
        logger.warning("API: Meeting not found. meeting_id=%s", meeting_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Meeting with ID {meeting_id} not found.",
        )
    risks = meeting.risks
    logger.info("API: Returning risks. meeting_id=%s, count=%d", meeting_id, len(risks))
    return risks

