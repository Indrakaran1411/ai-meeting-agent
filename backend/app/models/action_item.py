"""ActionItem model — AI-extracted tasks assigned during meetings."""

import uuid
from datetime import date, datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Date, DateTime, ForeignKey, Index, String, Text, func
from sqlalchemy.dialects.postgresql import ENUM, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import InsightStatus

if TYPE_CHECKING:
    from app.models.meeting import Meeting


class ActionItem(Base):
    """Represents an action item extracted by AI from a meeting transcript."""

    __tablename__ = "action_items"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    meeting_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("meetings.id", ondelete="CASCADE"),
        nullable=False,
    )
    description: Mapped[str] = mapped_column(
        Text, nullable=False, comment="Description of the action item"
    )
    assignee: Mapped[Optional[str]] = mapped_column(
        String(256), nullable=True, comment="Person responsible for this action"
    )
    due_date: Mapped[Optional[date]] = mapped_column(
        Date, nullable=True, comment="Deadline — nullable to prevent hallucinated dates"
    )
    verbatim_quote: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="Exact transcript quote supporting this action item"
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
    meeting: Mapped["Meeting"] = relationship(back_populates="action_items")

    __table_args__ = (
        Index("ix_action_items_meeting_id", "meeting_id"),
        Index("ix_action_items_status", "status"),
        Index("ix_action_items_assignee", "assignee"),
    )

    def __repr__(self) -> str:
        return f"<ActionItem(id={self.id!s}, assignee={self.assignee!r}, status={self.status!r})>"
