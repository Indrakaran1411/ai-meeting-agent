"""ChatSignal model — channel messages classified for actionable signals."""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Float, Index, String, Text, func
from sqlalchemy.dialects.postgresql import ENUM, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.enums import SignalType


class ChatSignal(Base):
    """Represents a chat message from Slack/Teams classified into an actionable signal category."""

    __tablename__ = "chat_signals"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    source: Mapped[str] = mapped_column(
        String(64), nullable=False, comment="Platform origin, e.g. slack, teams"
    )
    channel_id: Mapped[str] = mapped_column(
        String(256), nullable=False, comment="Channel or conversation identifier"
    )
    message_id: Mapped[str] = mapped_column(
        String(256), nullable=False, comment="Unique message identifier from the platform"
    )
    sender_name: Mapped[Optional[str]] = mapped_column(
        String(256), nullable=True, comment="Display name of the message sender"
    )
    content: Mapped[str] = mapped_column(
        Text, nullable=False, comment="Message text content"
    )
    signal_type: Mapped[SignalType] = mapped_column(
        ENUM(SignalType, name="signal_type", create_type=True),
        nullable=False,
        default=SignalType.GENERAL,
    )
    confidence: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True, comment="Classification confidence score (0.0–1.0)"
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

    __table_args__ = (
        Index("ix_chat_signals_signal_type", "signal_type"),
        Index("ix_chat_signals_channel_id", "channel_id"),
        Index("ix_chat_signals_created_at", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<ChatSignal(id={self.id!s}, signal_type={self.signal_type!r}, channel={self.channel_id!r})>"
