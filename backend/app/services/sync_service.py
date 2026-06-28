"""
Sync Service module responsible for preparing outbound Project Management (PM) payloads.
Performs data mapping and Pydantic validation cleanly without persistence or side effects.
"""

from datetime import datetime, timezone
import logging
from typing import List

from app.models import Meeting, ActionItem, Decision, Risk
from app.schemas.sync import (
    MeetingSyncPayload,
    ActionItemSyncPayload,
    DecisionSyncPayload,
    RiskSyncPayload
)

# Setup structured logger
logger = logging.getLogger("app.services.sync_service")


class SyncService:
    """Service class for formatting meeting insights into validated PM payloads."""

    @classmethod
    def build_meeting_sync_payload(
        cls,
        meeting: Meeting,
        action_items: List[ActionItem],
        decisions: List[Decision],
        risks: List[Risk]
    ) -> MeetingSyncPayload:
        """
        Maps DB ORM models to outgoing Pydantic payload models.
        All outbound fields are strictly validated against T10.2 constraints.

        Args:
            meeting: The Meeting ORM entity.
            action_items: List of ActionItem ORM entities to sync.
            decisions: List of Decision ORM entities to sync.
            risks: List of Risk ORM entities to sync.

        Returns:
            MeetingSyncPayload: A validated, serialized sync payload.
        """
        logger.info(
            "SyncService: Starting outbound payload compilation. meeting_id=%s, action_items=%d, decisions=%d, risks=%d",
            meeting.id,
            len(action_items),
            len(decisions),
            len(risks)
        )

        # 1. Map action items
        mapped_action_items = []
        for item in action_items:
            try:
                mapped_item = ActionItemSyncPayload(
                    id=item.id,
                    description=item.description,
                    assignee=item.assignee,
                    due_date=item.due_date
                )
                mapped_action_items.append(mapped_item)
            except Exception as e:
                logger.error(
                    "SyncService: Failed to map ActionItem to payload. action_item_id=%s, error=%s",
                    getattr(item, "id", "unknown"),
                    str(e)
                )
                raise

        # 2. Map decisions
        mapped_decisions = []
        for item in decisions:
            try:
                mapped_item = DecisionSyncPayload(
                    id=item.id,
                    description=item.description,
                    rationale=item.rationale
                )
                mapped_decisions.append(mapped_item)
            except Exception as e:
                logger.error(
                    "SyncService: Failed to map Decision to payload. decision_id=%s, error=%s",
                    getattr(item, "id", "unknown"),
                    str(e)
                )
                raise

        # 3. Map risks
        mapped_risks = []
        for item in risks:
            try:
                mapped_item = RiskSyncPayload(
                    id=item.id,
                    description=item.description,
                    severity=item.severity,
                    mitigation=item.mitigation
                )
                mapped_risks.append(mapped_item)
            except Exception as e:
                logger.error(
                    "SyncService: Failed to map Risk to payload. risk_id=%s, error=%s",
                    getattr(item, "id", "unknown"),
                    str(e)
                )
                raise

        # 4. Construct the consolidated MeetingSyncPayload
        try:
            payload = MeetingSyncPayload(
                meeting_id=meeting.id,
                title=meeting.title,
                summary=meeting.summary,
                action_items=mapped_action_items,
                decisions=mapped_decisions,
                risks=mapped_risks,
                generated_at=datetime.now(timezone.utc)
            )
            logger.info("SyncService: Outbound payload compiled successfully. meeting_id=%s", meeting.id)
            return payload
        except Exception as e:
            logger.error(
                "SyncService: Failed to construct consolidated MeetingSyncPayload. meeting_id=%s, error=%s",
                meeting.id,
                str(e)
            )
            raise
