"""Decision model — AI-extracted decisions made during meetings."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, ForeignKey, Index, Text, func
from sqlalchemy.dialects.postgresql import ENUM, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import InsightStatus

if TYPE_CHECKING:
    from app.models.meeting import Meeting


class Decision(Base):
    """Represents a decision extracted by AI from a meeting transcript."""

    __tablename__ = "decisions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    meeting_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("meetings.id", ondelete="CASCADE"),
        nullable=False,
    )
    description: Mapped[str] = mapped_column(
        Text, nullable=False, comment="Summary of the decision"
    )
    rationale: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="Reasoning behind the decision"
    )
    verbatim_quote: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="Exact transcript quote supporting this decision"
    )
    status: Mapped[InsightStatus] = mapped_column(
        ENUM(InsightStatus, name="insight_status", create_type=True),
        nullable=False,
        default=InsightStatus.DRAFT,
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
    meeting: Mapped["Meeting"] = relationship(back_populates="decisions")

    __table_args__ = (
        Index("ix_decisions_meeting_id", "meeting_id"),
        Index("ix_decisions_status", "status"),
    )

    def __repr__(self) -> str:
        return f"<Decision(id={self.id!s}, status={self.status!r})>"
