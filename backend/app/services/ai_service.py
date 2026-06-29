"""Service layer wrapping the Google GenAI SDK to interact with Gemini."""

import logging
import threading
import time
from typing import Optional

from google import genai
from google.genai import types

from app.core.config import settings
from app.schemas.meeting_analysis import MeetingAnalysis

logger = logging.getLogger("app.services.ai_service")


class AIServiceError(Exception):
    """Exception raised when the Gemini AI analysis service fails."""
    pass


class AIService:
    """
    Thread-safe, lazy-loaded singleton wrapper for the Google Gemini GenAI Client.
    Communicates with Gemini using the google-genai SDK to generate structured output.
    """
    _client: Optional[genai.Client] = None
    _lock = threading.Lock()

    @classmethod
    def get_client(cls) -> genai.Client:
        """Retrieves or initializes the lazy-loaded Gemini SDK client."""
        if cls._client is None:
            with cls._lock:
                if cls._client is None:
                    api_key = settings.GEMINI_API_KEY
                    if not api_key:
                        logger.error("AIService: GEMINI_API_KEY is not configured in settings.")
                        raise AIServiceError("GEMINI_API_KEY is not configured in settings.")
                    
                    logger.info("AIService: Initializing Google GenAI Client.")
                    cls._client = genai.Client(api_key=api_key)
        return cls._client

    @classmethod
    async def generate_analysis(
        cls,
        transcript: str,
        system_instruction: str,
        meeting_id: str = "N/A",
        task_id: str = "N/A"
    ) -> MeetingAnalysis:
        """
        Sends the transcript and system instructions to Gemini.
        Requests a structured response validating against the MeetingAnalysis schema.
        Runs asynchronously using client.aio.
        """
        client = cls.get_client()
        model_name = settings.GEMINI_MODEL

        logger.info(
            "AIService: Sending transcription content to Gemini API. "
            "meeting_id=%s, task_id=%s, model=%s, temperature=%.2f, max_tokens=%s",
            meeting_id,
            task_id,
            model_name,
            settings.GEMINI_TEMPERATURE,
            settings.GEMINI_MAX_OUTPUT_TOKENS,
        )

        start_time = time.perf_counter()

        try:
            # We configure Gemini to return a structured JSON response that strictly complies
            # with our Pydantic schema (MeetingAnalysis). By enforcing this constraint at the SDK level,
            # Gemini dynamically shapes its token generation to conform to the schema syntax,
            # eliminating the need for manual parsing, regex cleanup, or self-correction loops.
            config = types.GenerateContentConfig(
                system_instruction=system_instruction,
                response_mime_type="application/json",
                response_schema=MeetingAnalysis,
                temperature=settings.GEMINI_TEMPERATURE,
                max_output_tokens=settings.GEMINI_MAX_OUTPUT_TOKENS,
            )

            # We use client.aio for fully non-blocking asynchronous calls to the Google Gemini GenAI API,
            # ensuring that the worker event loop thread is never stalled waiting for network I/O.
            response = await client.aio.models.generate_content(
                model=model_name,
                contents=transcript,
                config=config,
            )

            latency = time.perf_counter() - start_time

            # Log tokens if usage metadata is available
            prompt_tokens = None
            completion_tokens = None
            if response.usage_metadata:
                prompt_tokens = response.usage_metadata.prompt_token_count
                completion_tokens = response.usage_metadata.candidates_token_count

            logger.info(
                "AIService: Gemini API call completed successfully. "
                "meeting_id=%s, task_id=%s, model=%s, latency=%.3fs, prompt_tokens=%s, completion_tokens=%s",
                meeting_id,
                task_id,
                model_name,
                latency,
                prompt_tokens if prompt_tokens is not None else "N/A",
                completion_tokens if completion_tokens is not None else "N/A",
            )

            # Retrieve parsed structured object directly from the response
            parsed_result = response.parsed
            if not parsed_result or not isinstance(parsed_result, MeetingAnalysis):
                import json
                raw_text = response.text
                if not raw_text:
                    raise AIServiceError("Gemini returned empty text response.")
                parsed_json = json.loads(raw_text)
                parsed_result = MeetingAnalysis.model_validate(parsed_json)

            return parsed_result

        except Exception as e:
            latency = time.perf_counter() - start_time
            logger.error(
                "AIService: Gemini API call failed. "
                "meeting_id=%s, task_id=%s, model=%s, latency=%.3fs, error=%s",
                meeting_id,
                task_id,
                model_name,
                latency,
                str(e),
                exc_info=True,
            )
            raise AIServiceError(f"Gemini generation failed: {e}") from e
