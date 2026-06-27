"""Transcript model — individual segments of a meeting transcription."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, Float, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.meeting import Meeting


class Transcript(Base):
    """Represents a single segment of a meeting transcript, tied to a speaker and time range."""

    __tablename__ = "transcripts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    meeting_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("meetings.id", ondelete="CASCADE"),
        nullable=False,
    )
    segment_index: Mapped[int] = mapped_column(
        Integer, nullable=False, comment="Order of this segment within the transcript"
    )
    speaker: Mapped[Optional[str]] = mapped_column(
        String(256), nullable=True, comment="Identified speaker name or label"
    )
    content: Mapped[str] = mapped_column(
        Text, nullable=False, comment="Transcribed text content"
    )
    start_time: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True, comment="Segment start time in seconds"
    )
    end_time: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True, comment="Segment end time in seconds"
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
    meeting: Mapped["Meeting"] = relationship(back_populates="transcripts")

    __table_args__ = (
        Index("ix_transcripts_meeting_id", "meeting_id"),
        Index("ix_transcripts_segment_index", "meeting_id", "segment_index"),
    )

    def __repr__(self) -> str:
        return f"<Transcript(id={self.id!s}, meeting_id={self.meeting_id!s}, segment={self.segment_index})>"
