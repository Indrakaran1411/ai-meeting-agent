"""Service layer handling speech-to-text transcription using Faster-Whisper."""

import logging
import os
import threading
import time
from pathlib import Path
from typing import Any, Generator, List, Tuple

import numpy as np
from faster_whisper import WhisperModel

from app.core.config import settings

logger = logging.getLogger("app.services.transcription_service")


class TranscriptionService:
    """
    Service class implementing a lazy-loaded, thread-safe Faster-Whisper model singleton.
    Provides methods to validate audio files, perform model warmup, and transcribe audio.
    """

    _model: WhisperModel = None
    _lock = threading.Lock()
    _warmed_up = False

    # Supported audio file extensions
    SUPPORTED_EXTENSIONS = {".mp3", ".wav", ".m4a"}

    @classmethod
    def get_model(cls) -> WhisperModel:
        """
        Retrieves the singleton WhisperModel instance, initializing it in a thread-safe
        manner if it does not already exist, and warming it up.
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
                    cls._warmup_model()
        return cls._model

    @classmethod
    def _warmup_model(cls) -> None:
        """
        Performs a lightweight warmup inference using 1 second of silence (zero array)
        to trigger graph compilation and avoid first-run latency.
        """
        if not cls._warmed_up and cls._model is not None:
            logger.info("TranscriptionService: Starting model warmup run...")
            start_time = time.perf_counter()
            # 1 second of silence at 16kHz sampling rate
            warmup_audio = np.zeros(16000, dtype=np.float32)
            try:
                # Run transcription on silence (generator must be iterated to execute)
                segments, _ = cls._model.transcribe(warmup_audio, beam_size=1)
                list(segments)
                cls._warmed_up = True
                warmup_duration = time.perf_counter() - start_time
                logger.info(
                    "TranscriptionService: Model warmup completed successfully in %.3f seconds.",
                    warmup_duration,
                )
            except Exception as e:
                logger.error(
                    "TranscriptionService: Warmup run failed. Error: %s",
                    str(e),
                    exc_info=True,
                )

    @classmethod
    def validate_audio_file(cls, file_path: str) -> None:
        """
        Validates the audio file path before initiating transcription.
        Verifies existence, non-zero size, extension support, and read permissions.
        Raises ValueError or FileNotFoundError if validation fails.
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
    ) -> Tuple[List[Any], Any]:
        """
        Transcribes a local audio file and returns the list of segments and transcription info.
        Integrates structured logging with meeting_id, task_id, and transcription details.
        """
        # Validate the audio file
        cls.validate_audio_file(file_path)

        # Retrieve the singleton model (loads/warms up if needed)
        model = cls.get_model()

        language_param = settings.WHISPER_LANGUAGE if settings.WHISPER_LANGUAGE else None

        logger.info(
            "TranscriptionService: Starting transcription. meeting_id=%s, task_id=%s, audio_file=%s, "
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

            # Consume the generator to perform actual transcription in memory
            segments = list(segments_generator)
            
            transcription_duration = time.perf_counter() - start_time
            segment_count = len(segments)
            audio_duration = getattr(info, "duration", 0.0)

            logger.info(
                "TranscriptionService: Transcription completed. meeting_id=%s, task_id=%s, audio_file=%s, "
                "model_size=%s, device=%s, compute_type=%s, "
                "transcription_time_seconds=%.3f, audio_duration_seconds=%.3f, segment_count=%d",
                meeting_id,
                task_id,
                file_path,
                settings.WHISPER_MODEL_SIZE,
                settings.WHISPER_DEVICE,
                settings.WHISPER_COMPUTE_TYPE,
                transcription_duration,
                audio_duration,
                segment_count,
            )

            return segments, info

        except Exception as e:
            logger.error(
                "TranscriptionService: Transcription failed. meeting_id=%s, task_id=%s, audio_file=%s. Error: %s",
                meeting_id,
                task_id,
                file_path,
                str(e),
                exc_info=True,
            )
            raise e
