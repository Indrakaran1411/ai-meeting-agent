"""
SyncLog Service — handles idempotency detection, audit persistence, and
payload hashing for the PM webhook sync pipeline.

Responsibilities:
  - Compute a deterministic SHA-256 hash of a serialized MeetingSyncPayload.
  - Check whether a SUCCESS record already exists (idempotency guard).
  - Insert a PENDING SyncLog before dispatch begins.
  - Update the SyncLog to SUCCESS or FAILED after dispatch completes.

This service performs only database operations. It does NOT call webhooks.
"""

import hashlib
import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.sync_log import SyncLog
from app.models.enums import SyncStatus
from app.schemas.sync import MeetingSyncPayload
from app.schemas.sync import WebhookDispatchResult

logger = logging.getLogger("app.services.sync_log_service")


class SyncLogService:
    """Service handling SyncLog persistence and idempotency checks."""

    # --------------------------------------------------------------------------
    # Hashing
    # --------------------------------------------------------------------------

    @staticmethod
    def compute_payload_hash(payload: MeetingSyncPayload) -> str:
        """Compute a deterministic SHA-256 hex digest of the serialized payload.

        The payload is serialized with mode='json' (datetime → ISO string, UUID
        → string) and then sorted to guarantee key ordering stability.
        The `generated_at` timestamp field is intentionally excluded from the
        hash so that retrying a sync for unchanged meeting data produces the
        same hash regardless of when the request is made.

        Args:
            payload: The MeetingSyncPayload to hash.

        Returns:
            A 64-character lowercase SHA-256 hex string.
        """
        # Hashing Design Decisions:
        # 1. Pydantic mode='json' converts UUIDs and datetime objects to their standardized
        #    string representation (e.g. ISO 8601), eliminating class serialization variations.
        raw = payload.model_dump(mode="json")
        
        # 2. Exclude `generated_at` because it records the request dispatch time. If the same meeting
        #    content is synced multiple times, the temporal metadata changes but the logical data
        #    remains identical. Removing it guarantees hash stability.
        raw.pop("generated_at", None)
        
        # 3. Sort keys lexicographically and strip whitespace from delimiters (separators=(",", ":")).
        #    This guards against Python version dictionary ordering discrepancies or formatting differences,
        #    producing a 100% deterministic string representation.
        serialized = json.dumps(raw, sort_keys=True, separators=(",", ":"))
        digest = hashlib.sha256(serialized.encode("utf-8")).hexdigest()
        logger.debug(
            "SyncLogService: Computed payload hash. meeting_id=%s, hash=%s",
            payload.meeting_id,
            digest,
        )
        return digest

    # --------------------------------------------------------------------------
    # Idempotency
    # --------------------------------------------------------------------------

    @staticmethod
    async def find_successful_sync(
        db: AsyncSession,
        meeting_id: uuid.UUID,
        payload_hash: str,
    ) -> Optional[SyncLog]:
        """Check whether a SUCCESS SyncLog already exists for this exact payload.

        Args:
            db: Async database session.
            meeting_id: UUID of the meeting being synced.
            payload_hash: SHA-256 hash of the payload to check.

        Returns:
            The existing SyncLog if found, else None.
        """
        stmt = (
            select(SyncLog)
            .where(
                SyncLog.meeting_id == meeting_id,
                SyncLog.payload_hash == payload_hash,
                SyncLog.status == SyncStatus.SUCCESS,
            )
            .limit(1)
        )
        result = await db.execute(stmt)
        existing = result.scalar_one_or_none()
        if existing:
            logger.info(
                "SyncLogService: Duplicate payload detected — SUCCESS record exists. "
                "meeting_id=%s, payload_hash=%s, sync_log_id=%s",
                meeting_id,
                payload_hash,
                existing.id,
            )
        return existing

    # --------------------------------------------------------------------------
    # Persistence
    # --------------------------------------------------------------------------

    @staticmethod
    async def create_pending(
        db: AsyncSession,
        *,
        meeting_id: uuid.UUID,
        payload_hash: str,
        webhook_url: Optional[str],
        request_id: Optional[str],
    ) -> SyncLog:
        """Insert a new SyncLog record with status=PENDING.

        This is called immediately before the webhook dispatch begins so that
        every attempt is recorded even if the process crashes mid-flight.

        Args:
            db: Async database session.
            meeting_id: UUID of the meeting being synced.
            payload_hash: SHA-256 hash of the payload.
            webhook_url: The configured target webhook URL (may be None).
            request_id: Correlation ID from the originating request.

        Returns:
            The newly created SyncLog ORM instance.
        """
        sync_log = SyncLog(
            meeting_id=meeting_id,
            request_id=request_id,
            webhook_url=webhook_url,
            status=SyncStatus.PENDING,
            payload_hash=payload_hash,
        )
        db.add(sync_log)
        try:
            await db.commit()
            await db.refresh(sync_log)
            logger.info(
                "SyncLogService: PENDING SyncLog created. sync_log_id=%s, meeting_id=%s",
                sync_log.id,
                meeting_id,
            )
            return sync_log
        except Exception:
            await db.rollback()
            logger.exception(
                "SyncLogService: Failed to create PENDING SyncLog. meeting_id=%s",
                meeting_id,
            )
            raise

    @staticmethod
    async def mark_success(
        db: AsyncSession,
        sync_log: SyncLog,
        *,
        http_status: Optional[int],
        response_message: str,
    ) -> SyncLog:
        """Update an existing SyncLog to SUCCESS after a successful dispatch.

        Args:
            db: Async database session.
            sync_log: The SyncLog ORM instance to update.
            http_status: HTTP status code from the downstream response.
            response_message: Descriptive outcome message.

        Returns:
            The refreshed SyncLog.
        """
        sync_log.status = SyncStatus.SUCCESS
        sync_log.http_status = http_status
        sync_log.response_message = response_message
        sync_log.dispatched_at = datetime.now(timezone.utc)
        try:
            await db.commit()
            await db.refresh(sync_log)
            logger.info(
                "SyncLogService: SyncLog marked SUCCESS. sync_log_id=%s, http_status=%s",
                sync_log.id,
                http_status,
            )
            return sync_log
        except Exception:
            await db.rollback()
            logger.exception(
                "SyncLogService: Failed to mark SyncLog as SUCCESS. sync_log_id=%s",
                sync_log.id,
            )
            raise

    @staticmethod
    async def mark_failed(
        db: AsyncSession,
        sync_log: SyncLog,
        *,
        http_status: Optional[int],
        response_message: str,
    ) -> SyncLog:
        """Update an existing SyncLog to FAILED after a dispatch failure.

        Args:
            db: Async database session.
            sync_log: The SyncLog ORM instance to update.
            http_status: HTTP status code if available (None for timeouts/DNS errors).
            response_message: Descriptive failure message.

        Returns:
            The refreshed SyncLog.
        """
        sync_log.status = SyncStatus.FAILED
        sync_log.http_status = http_status
        sync_log.response_message = response_message
        sync_log.dispatched_at = datetime.now(timezone.utc)
        try:
            await db.commit()
            await db.refresh(sync_log)
            logger.info(
                "SyncLogService: SyncLog marked FAILED. sync_log_id=%s, http_status=%s, message=%r",
                sync_log.id,
                http_status,
                response_message,
            )
            return sync_log
        except Exception:
            await db.rollback()
            logger.exception(
                "SyncLogService: Failed to mark SyncLog as FAILED. sync_log_id=%s",
                sync_log.id,
            )
            raise

    # --------------------------------------------------------------------------
    # Convenience
    # --------------------------------------------------------------------------

    @staticmethod
    async def finalize(
        db: AsyncSession,
        sync_log: SyncLog,
        dispatch_result: WebhookDispatchResult,
    ) -> SyncLog:
        """Finalize a SyncLog record based on a WebhookDispatchResult.

        Delegates to mark_success or mark_failed based on dispatch_result.success.

        Args:
            db: Async database session.
            sync_log: The PENDING SyncLog to finalize.
            dispatch_result: Result returned by WebhookService.send_meeting_payload.

        Returns:
            The finalized SyncLog.
        """
        if dispatch_result.success:
            return await SyncLogService.mark_success(
                db,
                sync_log,
                http_status=dispatch_result.status_code,
                response_message=dispatch_result.message,
            )
        else:
            return await SyncLogService.mark_failed(
                db,
                sync_log,
                http_status=dispatch_result.status_code,
                response_message=dispatch_result.message,
            )
