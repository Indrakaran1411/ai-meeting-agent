"""Pydantic schemas for Meeting API validation."""

import uuid
from datetime import datetime, date
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict

from app.models.enums import MeetingStatus, InsightStatus, RiskSeverity



class MeetingCreate(BaseModel):
    """Schema for validating meeting creation request payloads."""
    title: str = Field(
        ..., 
        min_length=1, 
        max_length=512, 
        description="The title of the meeting"
    )
    consent_given: bool = Field(
        ..., 
        description="Mandatory consent flag confirming recording and processing permission"
    )
    meeting_date: Optional[datetime] = Field(
        default=None, 
        description="The timestamp when the meeting occurred"
    )
    source: Optional[str] = Field(
        default=None, 
        max_length=128, 
        description="Origin platform, e.g. Zoom, Teams, Upload"
    )
    duration_minutes: Optional[int] = Field(
        default=None, 
        ge=0, 
        description="Duration of the meeting in minutes"
    )
    file_path: Optional[str] = Field(
        default=None, 
        max_length=1024, 
        description="Local or remote path to the meeting file"
    )


class MeetingResponseLightweight(BaseModel):
    """Lightweight response schema for meeting ingestion."""
    meeting_id: uuid.UUID
    status: MeetingStatus
    message: str


class ActionItemResponse(BaseModel):
    """Schema for action item retrieval."""
    id: uuid.UUID
    meeting_id: uuid.UUID
    description: str
    assignee: Optional[str] = None
    due_date: Optional[date] = None
    verbatim_quote: Optional[str] = None
    status: InsightStatus
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DecisionResponse(BaseModel):
    """Schema for decision retrieval."""
    id: uuid.UUID
    meeting_id: uuid.UUID
    description: str
    rationale: Optional[str] = None
    verbatim_quote: Optional[str] = None
    status: InsightStatus
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RiskResponse(BaseModel):
    """Schema for risk retrieval."""
    id: uuid.UUID
    meeting_id: uuid.UUID
    description: str
    severity: RiskSeverity
    verbatim_quote: Optional[str] = None
    mitigation: Optional[str] = None
    status: InsightStatus
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MeetingSummaryResponse(BaseModel):
    """Schema for meeting summary retrieval."""
    meeting_id: uuid.UUID
    summary: Optional[str] = None


class MeetingDetailResponse(BaseModel):
    """Schema for full meeting detail retrieval."""
    id: uuid.UUID
    title: str
    meeting_date: Optional[datetime] = None
    duration_minutes: Optional[int] = None
    source: Optional[str] = None
    consent_given: bool
    status: MeetingStatus
    file_path: Optional[str] = None
    summary: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

