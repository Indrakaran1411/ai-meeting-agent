"""
Pydantic schemas defining the outbound data structures sent to downstream
Project Management (PM) systems (such as Jira, Linear, or webhook consumers).
All schemas are configured to be immutable (frozen) to ensure contract consistency.
"""

from datetime import datetime, date
import uuid
from typing import Optional, List, Literal
from pydantic import BaseModel, Field, ConfigDict
from app.models.enums import RiskSeverity


class ActionItemSyncPayload(BaseModel):
    """Outbound data payload representing a synchronized action item."""
    model_config = ConfigDict(frozen=True)

    id: uuid.UUID = Field(
        ...,
        description="Unique identifier of the action item insight",
        example="be3bba92-a0e1-4ad9-8872-7a99bc25e1b0"
    )
    description: str = Field(
        ...,
        description="Summarized task description",
        example="Deploy the similarity search backend to production"
    )
    assignee: Optional[str] = Field(
        default=None,
        description="Assigned team member username or name",
        example="Alice"
    )
    due_date: Optional[date] = Field(
        default=None,
        description="Task deadline date",
        example="2026-07-05"
    )


class DecisionSyncPayload(BaseModel):
    """Outbound data payload representing a synchronized decision."""
    model_config = ConfigDict(frozen=True)

    id: uuid.UUID = Field(
        ...,
        description="Unique identifier of the decision insight",
        example="366f35fd-c6b0-4ec4-9df6-138c2650f384"
    )
    description: str = Field(
        ...,
        description="Summary of the decision reached",
        example="Transition primary databases to PostgreSQL"
    )
    rationale: Optional[str] = Field(
        default=None,
        description="Contextual reasoning supporting the decision",
        example="Enables standard SQL similarity indexing with zero external infra overhead"
    )


class RiskSyncPayload(BaseModel):
    """Outbound data payload representing a synchronized risk or blocker."""
    model_config = ConfigDict(frozen=True)

    id: uuid.UUID = Field(
        ...,
        description="Unique identifier of the risk insight",
        example="59c96d38-7c2e-4f62-9359-6f35b94a581c"
    )
    description: str = Field(
        ...,
        description="Detailed risk or threat description",
        example="High dependency on upstream API latency"
    )
    severity: RiskSeverity = Field(
        ...,
        description="Assessed severity scale of the risk",
        example=RiskSeverity.HIGH
    )
    mitigation: Optional[str] = Field(
        default=None,
        description="Suggested mitigation strategy or contingency plan",
        example="Incorporate offline caching layers"
    )


class MeetingSyncPayload(BaseModel):
    """Consolidated outbound sync payload containing meeting metadata and approved insights."""
    model_config = ConfigDict(frozen=True)

    meeting_id: uuid.UUID = Field(
        ...,
        description="Unique identifier of the synced meeting",
        example="e64dee57-8d8d-4901-b107-9fc864d54c95"
    )
    title: str = Field(
        ...,
        description="Meeting title",
        example="Weekly Sync Meeting"
    )
    summary: Optional[str] = Field(
        default=None,
        description="AI-generated meeting summary text",
        example="The meeting focused on the upcoming shipment of the vector database..."
    )
    action_items: List[ActionItemSyncPayload] = Field(
        default_factory=list,
        description="List of synchronized action items"
    )
    decisions: List[DecisionSyncPayload] = Field(
        default_factory=list,
        description="List of synchronized decisions"
    )
    risks: List[RiskSyncPayload] = Field(
        default_factory=list,
        description="List of synchronized risks and blockers"
    )
    generated_at: datetime = Field(
        ...,
        description="Timezone-aware UTC timestamp indicating when the payload was generated",
        example="2026-06-28T12:00:00Z"
    )
    source: Literal["meeting-agent"] = Field(
        default="meeting-agent",
        description="System source identity sending this event payload"
    )
    schema_version: Literal["1.0"] = Field(
        default="1.0",
        description="Version identifier of the sync schema contract"
    )


class WebhookDispatchResult(BaseModel):
    """Schema representing the outcome result of an outbound webhook dispatch execution."""
    model_config = ConfigDict(frozen=True)

    success: bool = Field(
        ...,
        description="Indicates whether the dispatch POST completed successfully with a 2xx response status",
        example=True
    )
    status_code: Optional[int] = Field(
        default=None,
        description="HTTP response status code returned by the downstream webhook endpoint",
        example=200
    )
    message: str = Field(
        ...,
        description="Detailed contextual message describing the dispatch outcome or failure details",
        example="Payload dispatched successfully"
    )
    dispatched_at: datetime = Field(
        ...,
        description="Timezone-aware UTC timestamp when the dispatch attempt completed",
        example="2026-06-28T12:00:05Z"
    )
