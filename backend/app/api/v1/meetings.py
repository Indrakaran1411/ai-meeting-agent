"""API router for meeting upload."""

import logging
import os
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Response, status, Form, File, UploadFile, Query
from sqlalchemy.ext.asyncio import AsyncSession

import uuid
from typing import Optional, List
from app.db.database import get_db
from app.models.enums import MeetingStatus
from app.schemas.meeting import (
    MeetingResponseLightweight,
    MeetingDetailResponse,
    MeetingSummaryResponse,
    ActionItemResponse,
    DecisionResponse,
    RiskResponse,
    MeetingListResponse,
    MeetingListResponseItem,
    ActionItemUpdateRequest,
    DecisionUpdateRequest,
    RiskUpdateRequest,
    MeetingStatisticsResponse,
    DashboardResponse,
    ErrorResponse,
    MeetingSyncResponse,
    COMMON_ERRORS
)
from app.services.meeting_service import MeetingService
from app.services.storage_service import StorageService
from app.services.sync_service import SyncService
from app.services.webhook_service import WebhookService
from app.workers.tasks import process_meeting

# Setup structured logger
logger = logging.getLogger("app.api.v1.meetings")





def create_summary_preview(summary: Optional[str], max_length: int = 200) -> Optional[str]:
    """Helper to safely truncate meeting summaries for list previews."""
    if not summary:
        return None
    return summary if len(summary) <= max_length else summary[:max_length] + "..."


def map_to_list_item(item) -> MeetingListResponseItem:
    """Helper to map a Meeting ORM object to a MeetingListResponseItem DTO."""
    return MeetingListResponseItem(
        id=item.id,
        title=item.title,
        status=item.status,
        created_at=item.created_at,
        meeting_date=item.meeting_date,
        duration_minutes=item.duration_minutes,
        source=item.source,
        summary_preview=create_summary_preview(item.summary)
    )


# Initialize FastAPI APIRouter
router = APIRouter(tags=["Meetings"])


@router.post(
    "/meetings/upload",
    response_model=MeetingResponseLightweight,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Upload and register a new meeting",
    description="Registers a new meeting in the pipeline. Consent is mandatory.",
    response_description="Uploader registration successful, audio ingestion and AI processing enqueued asynchronously",
    responses=COMMON_ERRORS,
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
    "/dashboard",
    response_model=DashboardResponse,
    status_code=status.HTTP_200_OK,
    summary="Get consolidated dashboard data",
    description="Returns aggregate statistics, recent meetings (latest 5), and recent draft action items (latest 5).",
    tags=["Dashboard"],
    response_description="Consolidated dashboard statistics, recent meetings, and draft action items retrieved successfully",
    responses=COMMON_ERRORS,
)
async def get_dashboard(
    db: AsyncSession = Depends(get_db),
):
    logger.info("API: GET dashboard requested.")
    # 1. Fetch statistics
    stats = await MeetingService.get_meeting_statistics(db)

    # 2. Fetch recent meetings (latest 5)
    _, meetings = await MeetingService.get_paginated_meetings(db, limit=5, offset=0)

    # 3. Fetch recent action items in DRAFT status
    draft_action_items = await MeetingService.get_draft_action_items(db, limit=5)

    # 4. Map ORM meetings to list response DTOs
    recent_meetings_mapped = [map_to_list_item(item) for item in meetings]

    logger.info("API: Dashboard data compiled successfully.")
    return DashboardResponse(
        statistics=stats,
        recent_meetings=recent_meetings_mapped,
        recent_action_items=draft_action_items
    )


@router.get(
    "/meetings/stats",
    response_model=MeetingStatisticsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get aggregate meeting statistics",
    description="Calculates and returns aggregate statistics for meetings, action items, decisions, and risks.",
    response_description="Aggregate counts for meeting status states and total extracted insights retrieved successfully",
    responses=COMMON_ERRORS,
)
async def get_meeting_statistics(
    db: AsyncSession = Depends(get_db),
):
    logger.info("API: GET meeting statistics requested.")
    stats = await MeetingService.get_meeting_statistics(db)
    return stats


@router.get(
    "/meetings/search",
    response_model=MeetingListResponse,
    status_code=status.HTTP_200_OK,
    summary="Search and filter meetings",
    description="Search meeting titles and summaries with support for pagination, status, and source filters.",
    response_description="Paginated list of meetings matching search query and status/source filters retrieved successfully",
    responses=COMMON_ERRORS,
)
async def search_meetings(
    q: Optional[str] = Query(None, description="Search term for title or summary"),
    status: Optional[MeetingStatus] = Query(None, description="Filter meetings by processing status"),
    source: Optional[str] = Query(None, description="Filter meetings by source platform (case-insensitive)"),
    limit: int = Query(10, ge=1, le=100, description="Maximum number of records to return"),
    offset: int = Query(0, ge=0, description="Offset index for pagination"),
    db: AsyncSession = Depends(get_db),
):
    logger.info(
        "API: Searching meetings. q=%s, status=%s, source=%s, limit=%d, offset=%d",
        q or "None",
        status.value if status else "None",
        source or "None",
        limit,
        offset
    )
    total_count, items = await MeetingService.get_paginated_meetings(
        db,
        limit=limit,
        offset=offset,
        status=status,
        source=source,
        q=q
    )

    # Map ORM objects to MeetingListResponseItem DTOs cleanly
    response_items = [map_to_list_item(item) for item in items]

    logger.info(
        "API: Search completed. q=%s, status=%s, source=%s, limit=%d, offset=%d, total_count=%d",
        q or "None",
        status.value if status else "None",
        source or "None",
        limit,
        offset,
        total_count
    )
    return MeetingListResponse(total_count=total_count, items=response_items)


@router.get(
    "/meetings/{meeting_id}",
    response_model=MeetingDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Get full details of a specific meeting",
    description="Retrieves a meeting's metadata, processing status, and summary description.",
    response_description="Detailed meeting metadata and processing summary retrieved successfully",
    responses=COMMON_ERRORS,
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
    "/meetings/{meeting_id}/summary",
    response_model=MeetingSummaryResponse,
    status_code=status.HTTP_200_OK,
    summary="Get summary of a specific meeting",
    description="Retrieves only the AI-generated high-level summary paragraph for a meeting.",
    response_description="AI-generated executive summary retrieved successfully",
    responses=COMMON_ERRORS,
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
    "/meetings/{meeting_id}/action-items",
    response_model=List[ActionItemResponse],
    status_code=status.HTTP_200_OK,
    summary="Get action items of a specific meeting",
    description="Retrieves all AI-extracted action items associated with a meeting.",
    response_description="List of AI-extracted meeting action items retrieved successfully",
    responses=COMMON_ERRORS,
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
    "/meetings/{meeting_id}/decisions",
    response_model=List[DecisionResponse],
    status_code=status.HTTP_200_OK,
    summary="Get decisions of a specific meeting",
    description="Retrieves all AI-extracted decisions associated with a meeting.",
    response_description="List of AI-extracted meeting decisions retrieved successfully",
    responses=COMMON_ERRORS,
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
    "/meetings/{meeting_id}/risks",
    response_model=List[RiskResponse],
    status_code=status.HTTP_200_OK,
    summary="Get risks of a specific meeting",
    description="Retrieves all AI-extracted risks associated with a meeting.",
    response_description="List of AI-extracted meeting risks and blockers retrieved successfully",
    responses=COMMON_ERRORS,
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


@router.get(
    "/meetings",
    response_model=MeetingListResponse,
    status_code=status.HTTP_200_OK,
    summary="List paginated meetings",
    description="Retrieves a list of meetings sorted by created_at DESC with optional status and source filtering.",
    response_description="Paginated list of meeting metadata records retrieved successfully",
    responses=COMMON_ERRORS,
)
async def list_meetings(
    limit: int = Query(10, ge=1, le=100, description="Maximum number of records to return"),
    offset: int = Query(0, ge=0, description="Offset index for pagination"),
    status: Optional[MeetingStatus] = Query(None, description="Filter meetings by processing status"),
    source: Optional[str] = Query(None, description="Filter meetings by source platform (case-insensitive)"),
    db: AsyncSession = Depends(get_db),
):
    """
    Endpoint handler to retrieve a paginated listing of meetings.
    """
    logger.info(
        "API: Listing meetings. limit=%d, offset=%d, status=%s, source=%s",
        limit,
        offset,
        status.value if status else "None",
        source or "None"
    )
    total_count, items = await MeetingService.get_paginated_meetings(
        db,
        limit=limit,
        offset=offset,
        status=status,
        source=source
    )
    
    # Map ORM objects to MeetingListResponseItem DTOs cleanly
    response_items = [map_to_list_item(item) for item in items]

    logger.info("API: Returning paginated meetings. total_count=%d, item_count=%d", total_count, len(response_items))
    return MeetingListResponse(total_count=total_count, items=response_items)


@router.patch(
    "/action-items/{action_item_id}",
    response_model=ActionItemResponse,
    status_code=status.HTTP_200_OK,
    summary="Partially update an action item",
    description="Updates only the provided fields of a specific action item.",
    tags=["Action Items"],
    response_description="Action item updated successfully",
    responses=COMMON_ERRORS,
)
async def patch_action_item(
    action_item_id: uuid.UUID,
    payload: ActionItemUpdateRequest,
    db: AsyncSession = Depends(get_db),
):
    logger.info("API: PATCH action item. id=%s", action_item_id)
    update_dict = payload.model_dump(exclude_unset=True)
    
    updated_item = await MeetingService.update_action_item(db, action_item_id, update_dict)
    if not updated_item:
        logger.warning("API: Action item not found. id=%s", action_item_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Action item with ID {action_item_id} not found."
        )

    logger.info(
        "API: Action item updated. id=%s, meeting_id=%s, fields=%s",
        updated_item.id,
        updated_item.meeting_id,
        list(update_dict.keys())
    )
    return updated_item


@router.patch(
    "/decisions/{decision_id}",
    response_model=DecisionResponse,
    status_code=status.HTTP_200_OK,
    summary="Partially update a decision",
    description="Updates only the provided fields of a specific decision.",
    tags=["Decisions"],
    response_description="Decision updated successfully",
    responses=COMMON_ERRORS,
)
async def patch_decision(
    decision_id: uuid.UUID,
    payload: DecisionUpdateRequest,
    db: AsyncSession = Depends(get_db),
):
    logger.info("API: PATCH decision. id=%s", decision_id)
    update_dict = payload.model_dump(exclude_unset=True)

    updated_item = await MeetingService.update_decision(db, decision_id, update_dict)
    if not updated_item:
        logger.warning("API: Decision not found. id=%s", decision_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Decision with ID {decision_id} not found."
        )

    logger.info(
        "API: Decision updated. id=%s, meeting_id=%s, fields=%s",
        updated_item.id,
        updated_item.meeting_id,
        list(update_dict.keys())
    )
    return updated_item


@router.patch(
    "/risks/{risk_id}",
    response_model=RiskResponse,
    status_code=status.HTTP_200_OK,
    summary="Partially update a risk",
    description="Updates only the provided fields of a specific risk.",
    tags=["Risks"],
    response_description="Risk updated successfully",
    responses=COMMON_ERRORS,
)
async def patch_risk(
    risk_id: uuid.UUID,
    payload: RiskUpdateRequest,
    db: AsyncSession = Depends(get_db),
):
    logger.info("API: PATCH risk. id=%s", risk_id)
    update_dict = payload.model_dump(exclude_unset=True)

    updated_item = await MeetingService.update_risk(db, risk_id, update_dict)
    if not updated_item:
        logger.warning("API: Risk not found. id=%s", risk_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Risk with ID {risk_id} not found."
        )

    logger.info(
        "API: Risk updated. id=%s, meeting_id=%s, fields=%s",
        updated_item.id,
        updated_item.meeting_id,
        list(update_dict.keys())
    )
    return updated_item


@router.delete(
    "/action-items/{action_item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an action item",
    description="Deletes a specific action item from the database.",
    tags=["Action Items"],
    response_description="Action item deleted successfully (no content returned)",
    responses=COMMON_ERRORS,
)
async def delete_action_item(
    action_item_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    logger.info("API: DELETE action item. id=%s", action_item_id)
    deleted_item = await MeetingService.delete_action_item(db, action_item_id)
    if not deleted_item:
        logger.warning("API: Action item not found for deletion. id=%s", action_item_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Action item with ID {action_item_id} not found."
        )
    logger.info("API: Action item deleted successfully. id=%s", action_item_id)
    return


@router.delete(
    "/decisions/{decision_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a decision",
    description="Deletes a specific decision from the database.",
    tags=["Decisions"],
    response_description="Decision deleted successfully (no content returned)",
    responses=COMMON_ERRORS,
)
async def delete_decision(
    decision_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    logger.info("API: DELETE decision. id=%s", decision_id)
    deleted_item = await MeetingService.delete_decision(db, decision_id)
    if not deleted_item:
        logger.warning("API: Decision not found for deletion. id=%s", decision_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Decision with ID {decision_id} not found."
        )
    logger.info("API: Decision deleted successfully. id=%s", decision_id)
    return


@router.delete(
    "/risks/{risk_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a risk",
    description="Deletes a specific risk from the database.",
    tags=["Risks"],
    response_description="Risk deleted successfully (no content returned)",
    responses=COMMON_ERRORS,
)
async def delete_risk(
    risk_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    logger.info("API: DELETE risk. id=%s", risk_id)
    deleted_item = await MeetingService.delete_risk(db, risk_id)
    if not deleted_item:
        logger.warning("API: Risk not found for deletion. id=%s", risk_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Risk with ID {risk_id} not found."
        )
    logger.info("API: Risk deleted successfully. id=%s", risk_id)
    return


@router.post(
    "/meetings/{meeting_id}/sync",
    response_model=MeetingSyncResponse,
    status_code=status.HTTP_200_OK,
    summary="Sync a meeting to the PM webhook",
    description=(
        "Retrieves the specified meeting along with all its action items, decisions, and risks, "
        "builds a structured `MeetingSyncPayload`, and dispatches it to the configured PM webhook. "
        "Returns **HTTP 200** when the downstream receiver accepted the payload. "
        "Returns **HTTP 503** if the webhook is not configured, times out, encounters a connection "
        "error, or the receiver returns a non-2xx status. In all cases the response body is a "
        "`MeetingSyncResponse` — inspect `success`, `status_code`, and `message` for detail."
    ),
    response_description="Sync accepted by downstream webhook receiver",
    responses={
        200: {"model": MeetingSyncResponse, "description": "Payload accepted by downstream webhook receiver"},
        404: {"model": ErrorResponse, "description": "Meeting not found"},
        422: {"model": ErrorResponse, "description": "Unprocessable Entity — path parameter validation failed"},
        500: {"model": ErrorResponse, "description": "Internal Server Error — payload build failed unexpectedly"},
        503: {
            "model": MeetingSyncResponse,
            "description": (
                "Service Unavailable — PM_WEBHOOK_URL is not configured, the webhook timed out, "
                "a connection error occurred, or the receiver returned a non-2xx status"
            )
        },
    },
    tags=["Sync"],
)
async def sync_meeting(
    meeting_id: uuid.UUID,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    """
    POST /api/v1/meetings/{meeting_id}/sync

    Orchestrates the full sync pipeline:
      1. Retrieve meeting (404 if missing).
      2. Load action items, decisions, and risks via eager-loaded selectin relationships.
      3. Build an immutable MeetingSyncPayload via SyncService.
      4. Dispatch the payload to the configured PM webhook via WebhookService.
      5. Return a MeetingSyncResponse with the dispatch outcome.
    """
    logger.info(
        "API: Sync requested. meeting_id=%s",
        meeting_id
    )

    # Step 1 — Retrieve meeting (relationships are selectin-loaded automatically)
    meeting = await MeetingService.get_meeting_by_id(db, meeting_id)
    if not meeting:
        logger.warning("API: Meeting not found for sync. meeting_id=%s", meeting_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Meeting with ID {meeting_id} not found."
        )

    logger.info(
        "API: Meeting retrieved for sync. meeting_id=%s, title=%r, status=%s, "
        "action_items=%d, decisions=%d, risks=%d",
        meeting_id,
        meeting.title,
        meeting.status.value,
        len(meeting.action_items),
        len(meeting.decisions),
        len(meeting.risks),
    )

    # Step 2 — Build outbound payload via SyncService (pure mapping, no side effects)
    try:
        sync_payload = SyncService.build_meeting_sync_payload(
            meeting=meeting,
            action_items=list(meeting.action_items),
            decisions=list(meeting.decisions),
            risks=list(meeting.risks),
        )
    except Exception:
        logger.exception(
            "API: SyncService failed to build payload. meeting_id=%s", meeting_id
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to build sync payload. Check server logs for details."
        )

    logger.info(
        "API: Sync payload built successfully. meeting_id=%s, schema_version=%s",
        meeting_id,
        sync_payload.schema_version,
    )

    # Step 3 — Dispatch to PM webhook via WebhookService
    dispatch_result = await WebhookService.send_meeting_payload(sync_payload)

    logger.info(
        "API: Webhook dispatch completed. meeting_id=%s, success=%s, status_code=%s, message=%r",
        meeting_id,
        dispatch_result.success,
        dispatch_result.status_code,
        dispatch_result.message,
    )

    # Step 4 — Set HTTP status based on dispatch outcome; body is always MeetingSyncResponse
    if not dispatch_result.success:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        logger.warning(
            "API: Sync dispatch failed — returning HTTP 503. meeting_id=%s, message=%r",
            meeting_id,
            dispatch_result.message,
        )

    return MeetingSyncResponse(
        success=dispatch_result.success,
        meeting_id=meeting_id,
        status_code=dispatch_result.status_code,
        message=dispatch_result.message,
        dispatched_at=dispatch_result.dispatched_at,
    )
