"""Service layer handling speech-to-text transcription using Faster-Whisper."""

import logging
import os
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List

from faster_whisper import WhisperModel

from app.core.config import settings

logger = logging.getLogger("app.services.transcription_service")


@dataclass
class TranscriptionResult:
    """Dataclass holding materialized transcription results."""
    full_text: str
    detected_language: str
    audio_duration: float
    transcription_duration: float
    segments: List[Dict[str, Any]]


class TranscriptionService:
    """
    Service class implementing a lazy-loaded, thread-safe Faster-Whisper model singleton.
    Provides methods to validate audio files and transcribe audio.
    """

    _model: WhisperModel = None
    _lock = threading.Lock()

    # Supported audio file extensions
    SUPPORTED_EXTENSIONS = {".mp3", ".wav", ".m4a"}

    @classmethod
    def get_model(cls) -> WhisperModel:
        """
        Retrieves the singleton WhisperModel instance, initializing it in a thread-safe
        manner if it does not already exist.
        """
        if cls._model is None:
            with cls._lock:
                if cls._model is None:
                    logger.info(
                        "TranscriptionService: Initializing WhisperModel singleton. "
                        "model_size=%s, device=%s, compute_type=%s",
                        settings.WHISPER_MODEL_SIZE,
                        settings.WHISPER_DEVICE,
                        settings.WHISPER_COMPUTE_TYPE,
                    )
                    cls._model = WhisperModel(
                        settings.WHISPER_MODEL_SIZE,
                        device=settings.WHISPER_DEVICE,
                        compute_type=settings.WHISPER_COMPUTE_TYPE,
                    )
        return cls._model

    @classmethod
    def validate_audio_file(cls, file_path: str) -> None:
        """
        Validates the audio file path before initiating transcription.
        Verifies existence, non-zero size, extension support, and read permissions.
        Raises FileNotFoundError, PermissionError, or ValueError if validation fails.
        """
        path = Path(file_path)

        # 1. Existence check
        if not path.exists():
            raise FileNotFoundError(f"Audio file not found at path: {file_path}")

        # 2. File check
        if not path.is_file():
            raise ValueError(f"Path is not a valid file: {file_path}")

        # 3. Readability check
        if not os.access(path, os.R_OK):
            raise PermissionError(f"Audio file is not readable: {file_path}")

        # 4. Non-zero size check
        if path.stat().st_size == 0:
            raise ValueError(f"Audio file is empty (size is 0 bytes): {file_path}")

        # 5. Extension check
        suffix = path.suffix.lower()
        if suffix not in cls.SUPPORTED_EXTENSIONS:
            raise ValueError(
                f"Unsupported audio file extension '{suffix}'. Supported: {cls.SUPPORTED_EXTENSIONS}"
            )

        logger.info("TranscriptionService: Audio file validation passed for: %s", file_path)

    @classmethod
    def transcribe_file(
        cls, 
        file_path: str,
        meeting_id: str = "N/A",
        task_id: str = "N/A"
    ) -> TranscriptionResult:
        """
        Transcribes a local audio file and returns a materialized TranscriptionResult object.
        Integrates structured logging with meeting_id, task_id, and transcription details.
        """
        # 1. Validate existence of the audio file BEFORE loading the model
        cls.validate_audio_file(file_path)

        # 2. Retrieve the singleton model with explicit error handling for model loading failure
        try:
            model = cls.get_model()
        except Exception as model_err:
            logger.error(
                "TranscriptionService: Failed to load Whisper model. meeting_id=%s, task_id=%s. Error: %s",
                meeting_id,
                task_id,
                str(model_err),
                exc_info=True,
            )
            raise RuntimeError(f"Whisper model loading failed: {model_err}") from model_err

        language_param = settings.WHISPER_LANGUAGE if settings.WHISPER_LANGUAGE else None

        logger.info(
            "TranscriptionService: Starting transcription. meeting_id=%s, task_id=%s, file_path=%s, "
            "model_size=%s, device=%s, compute_type=%s, beam_size=%d, language=%s, vad_filter=%s",
            meeting_id,
            task_id,
            file_path,
            settings.WHISPER_MODEL_SIZE,
            settings.WHISPER_DEVICE,
            settings.WHISPER_COMPUTE_TYPE,
            settings.WHISPER_BEAM_SIZE,
            language_param,
            settings.WHISPER_VAD_FILTER,
        )

        start_time = time.perf_counter()

        try:
            # Call Faster-Whisper transcribe
            segments_generator, info = model.transcribe(
                file_path,
                beam_size=settings.WHISPER_BEAM_SIZE,
                language=language_param,
                vad_filter=settings.WHISPER_VAD_FILTER,
            )

            # Materialize the segments generator into a reusable list of dictionaries
            materialized_segments = []
            for seg in segments_generator:
                materialized_segments.append({
                    "start": seg.start,
                    "end": seg.end,
                    "text": seg.text,
                })

            transcription_duration = time.perf_counter() - start_time
            segment_count = len(materialized_segments)
            audio_duration = getattr(info, "duration", 0.0)
            detected_language = getattr(info, "language", "unknown")

            # Compute combined full text from materialized segments
            full_text = " ".join([s["text"].strip() for s in materialized_segments]).strip()

            # Log with required structured format
            logger.info(
                "TranscriptionService: Transcription completed successfully. "
                "meeting_id=%s, file_path=%s, model_size=%s, detected_language=%s, "
                "audio_duration=%.3f, transcription_duration=%.3f, segment_count=%d",
                meeting_id,
                file_path,
                settings.WHISPER_MODEL_SIZE,
                detected_language,
                audio_duration,
                transcription_duration,
                segment_count,
            )

            return TranscriptionResult(
                full_text=full_text,
                detected_language=detected_language,
                audio_duration=audio_duration,
                transcription_duration=transcription_duration,
                segments=materialized_segments,
            )

        except Exception as e:
            logger.error(
                "TranscriptionService: Transcription failed. meeting_id=%s, task_id=%s, file_path=%s. Error: %s",
                meeting_id,
                task_id,
                file_path,
                str(e),
                exc_info=True,
            )
            raise e
