"""SyncLog model — audit record for every webhook dispatch attempt."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import ENUM, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import SyncStatus

if TYPE_CHECKING:
    from app.models.meeting import Meeting


class SyncLog(Base):
    """Audit record for a single outbound PM webhook dispatch attempt.

    Enables:
    - Idempotency: duplicate payloads (same meeting_id + payload_hash) are
      detected and skipped when a SUCCESS record already exists.
    - Auditability: every dispatch attempt — including failures — is persisted.
    """

    __tablename__ = "sync_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    meeting_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("meetings.id", ondelete="CASCADE"),
        nullable=False,
        comment="FK to the meeting being synced"
    )
    request_id: Mapped[Optional[str]] = mapped_column(
        String(128), nullable=True, comment="Correlation request ID from the originating HTTP request"
    )
    webhook_url: Mapped[Optional[str]] = mapped_column(
        String(2048), nullable=True, comment="Target webhook URL used for this dispatch attempt"
    )
    status: Mapped[SyncStatus] = mapped_column(
        ENUM(SyncStatus, name="sync_status", create_type=True),
        nullable=False,
        default=SyncStatus.PENDING,
        comment="PENDING on insert, updated to SUCCESS or FAILED after dispatch"
    )
    http_status: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True, comment="HTTP response status code returned by the downstream receiver"
    )
    response_message: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="Contextual message from the dispatch outcome"
    )
    payload_hash: Mapped[Optional[str]] = mapped_column(
        String(64), nullable=True, comment="SHA-256 hex digest of the serialized JSON payload (for idempotency)"
    )
    dispatched_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True, comment="Timestamp when the dispatch completed (null while PENDING)"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(),
        comment="Timestamp when this audit record was created"
    )

    # Relationship back to meeting (no cascade load needed here)
    meeting: Mapped["Meeting"] = relationship(back_populates="sync_logs")

    __table_args__ = (
        Index("ix_sync_logs_meeting_id", "meeting_id"),
        Index("ix_sync_logs_status", "status"),
        Index("ix_sync_logs_payload_hash", "payload_hash"),
        # Composite index for idempotency queries: meeting_id + payload_hash + status
        Index("ix_sync_logs_idempotency", "meeting_id", "payload_hash", "status"),
    )

    def __repr__(self) -> str:
        return f"<SyncLog(id={self.id!s}, meeting_id={self.meeting_id!s}, status={self.status!r})>"
