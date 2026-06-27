"""Pydantic schemas for Meeting API validation."""

import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

from app.models.enums import MeetingStatus


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
