"""Risk model — AI-extracted risks identified during meetings."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, ForeignKey, Index, Text, func
from sqlalchemy.dialects.postgresql import ENUM, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import InsightStatus, RiskSeverity

if TYPE_CHECKING:
    from app.models.meeting import Meeting


class Risk(Base):
    """Represents a risk identified by AI from a meeting transcript."""

    __tablename__ = "risks"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    meeting_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("meetings.id", ondelete="CASCADE"),
        nullable=False,
    )
    description: Mapped[str] = mapped_column(
        Text, nullable=False, comment="Description of the identified risk"
    )
    severity: Mapped[RiskSeverity] = mapped_column(
        ENUM(RiskSeverity, name="risk_severity", create_type=True),
        nullable=False,
        default=RiskSeverity.MEDIUM,
    )
    verbatim_quote: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="Exact transcript quote supporting this risk"
    )
    mitigation: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="Suggested mitigation strategy"
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
    meeting: Mapped["Meeting"] = relationship(back_populates="risks")

    __table_args__ = (
        Index("ix_risks_meeting_id", "meeting_id"),
        Index("ix_risks_severity", "severity"),
        Index("ix_risks_status", "status"),
    )

    def __repr__(self) -> str:
        return f"<Risk(id={self.id!s}, severity={self.severity!r}, status={self.status!r})>"
