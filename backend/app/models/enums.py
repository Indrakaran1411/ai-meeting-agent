"""Enum definitions shared across database models."""

import enum


class MeetingStatus(str, enum.Enum):
    """Lifecycle status of a meeting through the ingestion pipeline."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class InsightStatus(str, enum.Enum):
    """Review lifecycle status for AI-extracted insights."""
    DRAFT = "draft"
    APPROVED = "approved"
    SYNCED = "synced"


class RiskSeverity(str, enum.Enum):
    """Severity classification for identified risks."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class SignalType(str, enum.Enum):
    """Classification categories for chat channel signals."""
    BLOCKER = "blocker"
    DECISION = "decision"
    RISK = "risk"
    GENERAL = "general"
