"""Pydantic schemas for Meeting API validation and response serialization."""

import uuid
from datetime import datetime, date
from typing import Optional, List, Any
from pydantic import BaseModel, Field, ConfigDict

from app.models.enums import MeetingStatus, InsightStatus, RiskSeverity, SignalType, SyncStatus


class ErrorDetail(BaseModel):
    """Detailed structure of an API error payload."""
    type: str = Field(
        ...,
        description="The programmatic category/type of the error",
        example="validation_error"
    )
    message: str = Field(
        ...,
        description="Human-readable description of what went wrong",
        example="Validation failed: Field required at body.title"
    )
    status_code: int = Field(
        ...,
        description="HTTP status code of the response",
        example=422
    )
    details: Optional[Any] = Field(
        default=None,
        description="Optional granular validation or contextual failure information"
    )


class ErrorResponse(BaseModel):
    """Envelope wrapping all error responses returned by the API."""
    error: ErrorDetail = Field(
        ...,
        description="Detailed metadata concerning the encountered failure"
    )


# Standardized HTTP error responses for OpenAPI documentation
COMMON_ERRORS = {
    400: {"model": ErrorResponse, "description": "Bad Request - Incomplete or invalid request data"},
    404: {"model": ErrorResponse, "description": "Not Found - The requested resource does not exist"},
    422: {"model": ErrorResponse, "description": "Unprocessable Entity - Request input validation failed"},
    500: {"model": ErrorResponse, "description": "Internal Server Error - An unexpected backend error occurred"}
}


class MeetingCreate(BaseModel):
    """Schema for validating meeting creation request payloads."""
    title: str = Field(
        ..., 
        min_length=1, 
        max_length=512, 
        description="The title of the meeting",
        example="Weekly Sync Meeting"
    )
    consent_given: bool = Field(
        ..., 
        description="Mandatory consent flag confirming recording and processing permission",
        example=True
    )
    meeting_date: Optional[datetime] = Field(
        default=None, 
        description="The timestamp when the meeting occurred",
        example="2026-06-28T12:00:00Z"
    )
    source: Optional[str] = Field(
        default=None, 
        max_length=128, 
        description="Origin platform, e.g. Zoom, Teams, Upload",
        example="Zoom"
    )
    duration_minutes: Optional[int] = Field(
        default=None, 
        ge=0, 
        description="Duration of the meeting in minutes",
        example=45
    )
    file_path: Optional[str] = Field(
        default=None, 
        max_length=1024, 
        description="Local or remote path to the meeting file",
        example="uploads/meetings/raw_file.mp3"
    )


class MeetingResponseLightweight(BaseModel):
    """Lightweight response schema returned immediately upon successfully starting the ingestion pipeline."""
    meeting_id: uuid.UUID = Field(
        ...,
        description="Unique identifier (UUID) assigned to the registered meeting",
        example="e64dee57-8d8d-4901-b107-9fc864d54c95"
    )
    status: MeetingStatus = Field(
        ...,
        description="Current processing pipeline status of the meeting",
        example=MeetingStatus.PENDING
    )
    message: str = Field(
        ...,
        description="Confirmation message detailing the ingestion state",
        example="Meeting registered successfully. Processing has been enqueued."
    )


class ActionItemResponse(BaseModel):
    """Schema representing an extracted meeting action item."""
    id: uuid.UUID = Field(
        ...,
        description="Unique identifier of the action item insight record",
        example="be3bba92-a0e1-4ad9-8872-7a99bc25e1b0"
    )
    meeting_id: uuid.UUID = Field(
        ...,
        description="UUID of the parent meeting record",
        example="e64dee57-8d8d-4901-b107-9fc864d54c95"
    )
    description: str = Field(
        ...,
        description="Summarized description of the action item task",
        example="Ship the vector database search feature by Monday."
    )
    assignee: Optional[str] = Field(
        default=None,
        max_length=256,
        description="Name of the team member assigned to this task",
        example="Alice"
    )
    due_date: Optional[date] = Field(
        default=None,
        description="Target deadline/due date of the task",
        example="2026-06-30"
    )
    verbatim_quote: Optional[str] = Field(
        default=None,
        description="Verbatim text quote from the meeting transcript validating this action item",
        example="Alice, we need to ship the vector database search feature by next Monday."
    )
    status: InsightStatus = Field(
        ...,
        description="Workflow review status of the action item",
        example=InsightStatus.DRAFT
    )
    created_at: datetime = Field(
        ...,
        description="Timestamp when the action item record was persisted",
        example="2026-06-28T12:00:00Z"
    )
    updated_at: datetime = Field(
        ...,
        description="Timestamp when the action item record was last updated",
        example="2026-06-28T12:30:00Z"
    )

    model_config = ConfigDict(from_attributes=True)


class DecisionResponse(BaseModel):
    """Schema representing an extracted meeting decision."""
    id: uuid.UUID = Field(
        ...,
        description="Unique identifier of the decision insight record",
        example="366f35fd-c6b0-4ec4-9df6-138c2650f384"
    )
    meeting_id: uuid.UUID = Field(
        ...,
        description="UUID of the parent meeting record",
        example="e64dee57-8d8d-4901-b107-9fc864d54c95"
    )
    description: str = Field(
        ...,
        description="Summarized description of the decision reached",
        example="Adopt pgvector for local vector similarity search."
    )
    rationale: Optional[str] = Field(
        default=None,
        description="Documented context/rationale backing the decision",
        example="Enables standard SQL similarity indexing with zero external infra overhead."
    )
    verbatim_quote: Optional[str] = Field(
        default=None,
        description="Verbatim text quote from the meeting transcript validating this decision",
        example="We will proceed with pgvector since it runs within our existing Postgres setup."
    )
    status: InsightStatus = Field(
        ...,
        description="Workflow review status of the decision",
        example=InsightStatus.DRAFT
    )
    created_at: datetime = Field(
        ...,
        description="Timestamp when the decision record was persisted",
        example="2026-06-28T12:00:00Z"
    )
    updated_at: datetime = Field(
        ...,
        description="Timestamp when the decision record was last updated",
        example="2026-06-28T12:30:00Z"
    )

    model_config = ConfigDict(from_attributes=True)


class RiskResponse(BaseModel):
    """Schema representing an extracted meeting risk or blocker."""
    id: uuid.UUID = Field(
        ...,
        description="Unique identifier of the risk insight record",
        example="59c96d38-7c2e-4f62-9359-6f35b94a581c"
    )
    meeting_id: uuid.UUID = Field(
        ...,
        description="UUID of the parent meeting record",
        example="e64dee57-8d8d-4901-b107-9fc864d54c95"
    )
    description: str = Field(
        ...,
        description="Summarized description of the identified risk or threat",
        example="Dependency on upstream LLM API latency."
    )
    severity: RiskSeverity = Field(
        ...,
        description="Assessed severity scale of the risk",
        example=RiskSeverity.HIGH
    )
    verbatim_quote: Optional[str] = Field(
        default=None,
        description="Verbatim text quote from the meeting transcript highlighting the risk",
        example="If the external API encounters downtime, our processing queue will stall."
    )
    mitigation: Optional[str] = Field(
        default=None,
        description="Suggested mitigation strategy or contingency plan",
        example="Introduce local fallback processing pipelines and offline queues."
    )
    status: InsightStatus = Field(
        ...,
        description="Workflow review status of the risk",
        example=InsightStatus.DRAFT
    )
    created_at: datetime = Field(
        ...,
        description="Timestamp when the risk record was persisted",
        example="2026-06-28T12:00:00Z"
    )
    updated_at: datetime = Field(
        ...,
        description="Timestamp when the risk record was last updated",
        example="2026-06-28T12:30:00Z"
    )

    model_config = ConfigDict(from_attributes=True)


class MeetingSummaryResponse(BaseModel):
    """Schema representing a meeting's executive AI summary description."""
    meeting_id: uuid.UUID = Field(
        ...,
        description="UUID of the corresponding meeting",
        example="e64dee57-8d8d-4901-b107-9fc864d54c95"
    )
    summary: Optional[str] = Field(
        default=None,
        description="Detailed text of the executive summary generated by AI",
        example="The meeting focused on the upcoming shipment of the vector database search feature..."
    )


class MeetingDetailResponse(BaseModel):
    """Schema representing detailed metadata and pipeline status for a specific meeting."""
    id: uuid.UUID = Field(
        ...,
        description="Unique identifier of the meeting",
        example="e64dee57-8d8d-4901-b107-9fc864d54c95"
    )
    title: str = Field(
        ...,
        description="Meeting title",
        example="Weekly Sync Meeting"
    )
    meeting_date: Optional[datetime] = Field(
        default=None,
        description="Timestamp when the meeting took place",
        example="2026-06-28T12:00:00Z"
    )
    duration_minutes: Optional[int] = Field(
        default=None,
        description="Uptime/duration of the meeting in minutes",
        example=45
    )
    source: Optional[str] = Field(
        default=None,
        description="Platform origin of the meeting recording",
        example="Zoom"
    )
    consent_given: bool = Field(
        ...,
        description="Consent confirmation flag authorizing meeting data processing",
        example=True
    )
    status: MeetingStatus = Field(
        ...,
        description="Current processing pipeline status of the meeting",
        example=MeetingStatus.COMPLETED
    )
    file_path: Optional[str] = Field(
        default=None,
        description="Local path to the saved audio resource file",
        example="uploads/meetings/raw_file.mp3"
    )
    summary: Optional[str] = Field(
        default=None,
        description="Extracted executive summary text",
        example="The meeting focused on the upcoming shipment of the vector database..."
    )
    created_at: datetime = Field(
        ...,
        description="Uploader registration timestamp",
        example="2026-06-28T12:00:00Z"
    )
    updated_at: datetime = Field(
        ...,
        description="Last metadata updates timestamp",
        example="2026-06-28T12:30:00Z"
    )

    model_config = ConfigDict(from_attributes=True)


class MeetingListResponseItem(BaseModel):
    """Schema representing a summarized meeting item returned in listings."""
    id: uuid.UUID = Field(
        ...,
        description="Unique identifier of the meeting",
        example="e64dee57-8d8d-4901-b107-9fc864d54c95"
    )
    title: str = Field(
        ...,
        description="Meeting title",
        example="Weekly Sync Meeting"
    )
    status: MeetingStatus = Field(
        ...,
        description="Processing status of the meeting",
        example=MeetingStatus.COMPLETED
    )
    created_at: datetime = Field(
        ...,
        description="Ingestion registration timestamp",
        example="2026-06-28T12:00:00Z"
    )
    meeting_date: Optional[datetime] = Field(
        default=None,
        description="Timestamp when the meeting took place",
        example="2026-06-28T12:00:00Z"
    )
    duration_minutes: Optional[int] = Field(
        default=None,
        description="Uptime/duration of the meeting in minutes",
        example=45
    )
    source: Optional[str] = Field(
        default=None,
        description="Platform origin of the meeting recording",
        example="Zoom"
    )
    summary_preview: Optional[str] = Field(
        default=None,
        description="Truncated (up to 200 chars) preview of the meeting summary description",
        example="The meeting focused on the upcoming shipment of the vector database..."
    )

    model_config = ConfigDict(from_attributes=True)


class MeetingListResponse(BaseModel):
    """Envelope wrapping a paginated listing of meetings."""
    total_count: int = Field(
        ...,
        description="Total database records matching query filters before applying pagination limits",
        example=42
    )
    items: List[MeetingListResponseItem] = Field(
        ...,
        description="Paginated list of matching meeting items"
    )


class ActionItemUpdateRequest(BaseModel):
    """Schema for validating action item partial updates."""
    description: Optional[str] = Field(
        default=None,
        min_length=1,
        description="Updated description of the action item",
        example="Deploy the similarity search backend to production."
    )
    assignee: Optional[str] = Field(
        default=None,
        max_length=256,
        description="Name of the team member assigned to this task",
        example="Alice"
    )
    due_date: Optional[date] = Field(
        default=None,
        description="Updated target deadline of the task",
        example="2026-07-05"
    )
    status: Optional[InsightStatus] = Field(
        default=None,
        description="Workflow state representing insight review state",
        example=InsightStatus.APPROVED
    )


class DecisionUpdateRequest(BaseModel):
    """Schema for validating decision partial updates."""
    description: Optional[str] = Field(
        default=None,
        min_length=1,
        description="Updated summary of the decision reached",
        example="Transition primary databases to PostgreSQL."
    )
    rationale: Optional[str] = Field(
        default=None,
        description="Updated context backing the decision",
        example="Avoids multi-infra sync errors and reduces hosting costs."
    )
    status: Optional[InsightStatus] = Field(
        default=None,
        description="Workflow state representing insight review state",
        example=InsightStatus.APPROVED
    )


class RiskUpdateRequest(BaseModel):
    """Schema for validating risk partial updates."""
    description: Optional[str] = Field(
        default=None,
        min_length=1,
        description="Updated description of the identified risk or blockers",
        example="High dependency on upstream API latency."
    )
    severity: Optional[RiskSeverity] = Field(
        default=None,
        description="Updated severity rating",
        example=RiskSeverity.HIGH
    )
    mitigation: Optional[str] = Field(
        default=None,
        description="Updated mitigation strategy",
        example="Incorporate offline caching layers."
    )
    status: Optional[InsightStatus] = Field(
        default=None,
        description="Workflow state representing insight review state",
        example=InsightStatus.APPROVED
    )


class MeetingStatisticsResponse(BaseModel):
    """Schema representing aggregate status counts for meetings and insights."""
    total_meetings: int = Field(
        ...,
        description="Aggregate count of all registered meetings",
        example=11
    )
    completed_meetings: int = Field(
        ...,
        description="Count of successfully processed meetings",
        example=9
    )
    processing_meetings: int = Field(
        ...,
        description="Count of meetings currently being processed",
        example=2
    )
    failed_meetings: int = Field(
        ...,
        description="Count of failed meeting processing attempts",
        example=0
    )
    pending_meetings: int = Field(
        ...,
        description="Count of pending meetings inside queue",
        example=0
    )
    total_action_items: int = Field(
        ...,
        description="Total action items extracted",
        example=5
    )
    total_decisions: int = Field(
        ...,
        description="Total decisions extracted",
        example=2
    )
    total_risks: int = Field(
        ...,
        description="Total risks/blockers extracted",
        example=2
    )

    model_config = ConfigDict(from_attributes=True)


class DashboardResponse(BaseModel):
    """Schema representing consolidated dashboard statistics, recent activities, and pending actions."""
    statistics: MeetingStatisticsResponse = Field(
        ...,
        description="Aggregate statistics for meetings and insights"
    )
    recent_meetings: List[MeetingListResponseItem] = Field(
        ...,
        description="Chronological list of the 5 most recent meetings"
    )
    recent_action_items: List[ActionItemResponse] = Field(
        ...,
        description="Chronological list of the 5 most recent action items still in draft workflow status"
    )


class HealthResponse(BaseModel):
    """Schema representing liveness check information."""
    status: str = Field(..., description="Liveness status of the API", example="healthy")
    service: str = Field(..., description="Service name identifier", example="meeting-agent")
    version: str = Field(..., description="Installed app version code", example="0.1.0")


class ReadyResponse(BaseModel):
    """Schema representing dependency readiness details."""
    status: str = Field(..., description="Readiness status of the API", example="ready")
    database: str = Field(..., description="Uptime status of PostgreSQL dependency", example="ok")
    redis: str = Field(..., description="Uptime status of Redis dependency", example="ok")


class MeetingSyncResponse(BaseModel):
    """Schema representing the outcome of a meeting synchronization request.

    For a successful first sync:
        success=True, skipped=False, sync_log_id=<uuid>

    For a duplicate payload (already synchronized):
        success=True, skipped=True, reason="Payload already synchronized."

    For a webhook failure:
        success=False, skipped=False, sync_log_id=<uuid>
    """
    model_config = ConfigDict(frozen=True)

    success: bool = Field(
        ...,
        description="Indicates whether the sync completed successfully",
        example=True
    )
    meeting_id: uuid.UUID = Field(
        ...,
        description="Unique identifier of the meeting synced",
        example="e64dee57-8d8d-4901-b107-9fc864d54c95"
    )
    status_code: Optional[int] = Field(
        default=None,
        description="HTTP status code returned by the downstream webhook endpoint",
        example=200
    )
    message: str = Field(
        ...,
        description="Contextual message describing the sync status",
        example="Payload successfully accepted by downstream webhook receiver"
    )
    dispatched_at: Optional[datetime] = Field(
        default=None,
        description="Timezone-aware UTC timestamp when the sync completed",
        example="2026-06-28T12:00:05Z"
    )
    sync_log_id: Optional[uuid.UUID] = Field(
        default=None,
        description="UUID of the SyncLog audit record created for this attempt",
        example="f3b1a2c4-5d6e-7f89-a012-b34c5d6e7f89"
    )
    skipped: bool = Field(
        default=False,
        description=(
            "True when dispatch was skipped because an identical payload was "
            "already successfully synchronized (idempotency guard)"
        ),
        example=False
    )
    reason: Optional[str] = Field(
        default=None,
        description="Human-readable explanation when skipped=True",
        example="Payload already synchronized."
    )


class TranscriptResponse(BaseModel):
    """Schema representing an individual transcript segment."""
    id: uuid.UUID
    meeting_id: uuid.UUID
    speaker: Optional[str] = Field(default=None, description="Display name of the speaker")
    content: str = Field(..., description="Transcribed content/text segment")
    segment_index: int = Field(..., description="Order index of segment in the transcript")
    start_time: float = Field(..., description="Start timestamp of segment in seconds")
    end_time: float = Field(..., description="End timestamp of segment in seconds")
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SyncLogResponse(BaseModel):
    """Schema representing a synchronization attempt log."""
    id: uuid.UUID
    meeting_id: uuid.UUID
    request_id: Optional[str] = Field(default=None, description="Correlation request ID")
    webhook_url: Optional[str] = Field(default=None, description="Target webhook URL")
    status: SyncStatus = Field(..., description="Outcome status of the synchronization")
    http_status: Optional[int] = Field(default=None, description="Downstream HTTP status code")
    response_message: Optional[str] = Field(default=None, description="Downstream response or error message")
    payload_hash: Optional[str] = Field(default=None, description="Payload hash for idempotency")
    dispatched_at: Optional[datetime] = Field(default=None, description="Timestamp when dispatch completed")
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ChatSignalResponse(BaseModel):
    """Schema representing a classified chat signal."""
    id: uuid.UUID
    source: str = Field(..., description="Platform origin (slack/teams/etc)")
    channel_id: str = Field(..., description="Channel or conversation identifier")
    message_id: str = Field(..., description="Unique message identifier from platform")
    sender_name: Optional[str] = Field(default=None, description="Display name of sender")
    content: str = Field(..., description="Message text content")
    signal_type: SignalType = Field(..., description="Signal classification category")
    confidence: Optional[float] = Field(default=None, description="Classification confidence rating")
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SemanticSearchResultItem(BaseModel):
    """Schema representing a single ranked result in a semantic vector search."""
    meeting: MeetingListResponseItem = Field(
        ...,
        description="The matching meeting metadata"
    )
    relevant_transcript_chunk: Optional[str] = Field(
        default=None,
        description="The transcript segment text that matched semantically, or None if matched the summary"
    )
    similarity_score: float = Field(
        ...,
        description="The cosine similarity score calculated as 1 - cosine_distance"
    )
    matching_summary: bool = Field(
        default=False,
        description="Flag indicating if the semantic match was on the meeting's high-level summary"
    )


class SemanticSearchResponse(BaseModel):
    """Schema representing the list of results returned from a semantic vector search query."""
    results: List[SemanticSearchResultItem] = Field(
        ...,
        description="Chronologically or similarity-ranked semantic search outcomes"
    )



