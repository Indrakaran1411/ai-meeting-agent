"""
Webhook Service module responsible for transmitting sync payloads to configured webhook endpoints.
Handles HTTP exceptions, request timeouts, and connection handshakes gracefully.
"""

import logging
import time
from datetime import datetime, timezone
from typing import Optional
import httpx

from app.core.config import settings
from app.schemas.sync import MeetingSyncPayload, WebhookDispatchResult

logger = logging.getLogger("app.services.webhook_service")


class WebhookService:
    """Service responsible for sending sync payloads to downstream webhooks."""

    _client: Optional[httpx.AsyncClient] = None

    @classmethod
    def get_client(cls) -> httpx.AsyncClient:
        """Returns a cached/shared AsyncClient configuration."""
        if cls._client is None or cls._client.is_closed:
            timeout_seconds = float(settings.PM_WEBHOOK_TIMEOUT)
            cls._client = httpx.AsyncClient(
                timeout=httpx.Timeout(timeout_seconds),
                headers={"Content-Type": "application/json"}
            )
        return cls._client

    @classmethod
    async def close_client(cls) -> None:
        """Closes the shared AsyncClient if initialized."""
        if cls._client is not None and not cls._client.is_closed:
            await cls._client.aclose()
            cls._client = None

    @classmethod
    async def send_meeting_payload(
        cls,
        payload: MeetingSyncPayload,
    ) -> WebhookDispatchResult:
        """
        Dispatches a MeetingSyncPayload to the configured downstream PM Agent webhook.

        Args:
            payload: The meeting sync payload validation schema.

        Returns:
            WebhookDispatchResult: The validated outcome of the dispatch attempt.
        """
        webhook_url = settings.PM_WEBHOOK_URL
        dispatched_at = datetime.now(timezone.utc)

        if not webhook_url:
            logger.warning(
                "WebhookService: PM_WEBHOOK_URL is not configured. Webhook dispatch skipped. meeting_id=%s",
                payload.meeting_id
            )
            return WebhookDispatchResult(
                success=False,
                status_code=None,
                message="PM_WEBHOOK_URL settings parameter is not configured",
                dispatched_at=dispatched_at
            )

        logger.info(
            "WebhookService: Initiating webhook payload transmission. target_url=%s, meeting_id=%s",
            webhook_url,
            payload.meeting_id
        )

        client = cls.get_client()
        serialized_payload = payload.model_dump(mode="json")
        start_time = time.perf_counter()

        try:
            response = await client.post(webhook_url, json=serialized_payload)
            elapsed_ms = (time.perf_counter() - start_time) * 1000

            logger.info(
                "WebhookService: Webhook POST response received. status_code=%d, elapsed_time=%.2fms, meeting_id=%s",
                response.status_code,
                elapsed_ms,
                payload.meeting_id
            )

            if 200 <= response.status_code < 300:
                return WebhookDispatchResult(
                    success=True,
                    status_code=response.status_code,
                    message="Payload successfully accepted by downstream webhook receiver",
                    dispatched_at=datetime.now(timezone.utc)
                )
            else:
                return WebhookDispatchResult(
                    success=False,
                    status_code=response.status_code,
                    message=f"Receiver returned HTTP error response status code: {response.status_code}",
                    dispatched_at=datetime.now(timezone.utc)
                )

        except httpx.TimeoutException as exc:
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            logger.error(
                "WebhookService: Webhook POST failed due to timeout. timeout_configured=%d seconds, elapsed_time=%.2fms, error=%s, meeting_id=%s",
                settings.PM_WEBHOOK_TIMEOUT,
                elapsed_ms,
                str(exc),
                payload.meeting_id
            )
            return WebhookDispatchResult(
                success=False,
                status_code=None,
                message=f"Connection attempt timed out after {settings.PM_WEBHOOK_TIMEOUT} seconds",
                dispatched_at=datetime.now(timezone.utc)
            )

        except httpx.ConnectError as exc:
            logger.error(
                "WebhookService: Webhook POST failed due to connection error (DNS/network down). error=%s, meeting_id=%s",
                str(exc),
                payload.meeting_id
            )
            return WebhookDispatchResult(
                success=False,
                status_code=None,
                message="DNS lookup or connection handshake failed",
                dispatched_at=datetime.now(timezone.utc)
            )

        except Exception as exc:
            logger.exception(
                "WebhookService: Unexpected exception encountered during webhook dispatch. meeting_id=%s",
                payload.meeting_id
            )
            return WebhookDispatchResult(
                success=False,
                status_code=None,
                message="Unexpected transport exception occurred",
                dispatched_at=datetime.now(timezone.utc)
            )
