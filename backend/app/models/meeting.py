"""Meeting model — central entity representing an uploaded meeting."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, Index, Integer, String, Text, Boolean, func
from sqlalchemy.dialects.postgresql import ENUM, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import MeetingStatus

if TYPE_CHECKING:
    from app.models.action_item import ActionItem
    from app.models.decision import Decision
    from app.models.risk import Risk
    from app.models.sync_log import SyncLog
    from app.models.transcript import Transcript


class Meeting(Base):
    """Represents an uploaded meeting with its metadata and processing status."""

    __tablename__ = "meetings"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    meeting_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    duration_minutes: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True
    )
    source: Mapped[Optional[str]] = mapped_column(
        String(128), nullable=True, comment="Origin platform, e.g. Zoom, Teams, Upload"
    )
    consent_given: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    status: Mapped[MeetingStatus] = mapped_column(
        ENUM(MeetingStatus, name="meeting_status", create_type=True),
        nullable=False,
        default=MeetingStatus.PENDING,
    )
    file_path: Mapped[Optional[str]] = mapped_column(
        String(1024), nullable=True, comment="Path to uploaded audio/video file"
    )
    summary: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="AI-generated meeting summary"
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    # Relationships
    transcripts: Mapped[list["Transcript"]] = relationship(
        back_populates="meeting", cascade="all, delete-orphan", lazy="selectin"
    )
    action_items: Mapped[list["ActionItem"]] = relationship(
        back_populates="meeting", cascade="all, delete-orphan", lazy="selectin"
    )
    decisions: Mapped[list["Decision"]] = relationship(
        back_populates="meeting", cascade="all, delete-orphan", lazy="selectin"
    )
    risks: Mapped[list["Risk"]] = relationship(
        back_populates="meeting", cascade="all, delete-orphan", lazy="selectin"
    )
    sync_logs: Mapped[list["SyncLog"]] = relationship(
        back_populates="meeting", cascade="all, delete-orphan", lazy="select"
    )

    __table_args__ = (
        Index("ix_meetings_status", "status"),
        Index("ix_meetings_meeting_date", "meeting_date"),
        Index("ix_meetings_created_at", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<Meeting(id={self.id!s}, title={self.title!r}, status={self.status!r})>"
