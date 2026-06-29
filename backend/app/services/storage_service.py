"""Storage service layer handling file validation, size limits, naming, and disk storage."""

import logging
import os
import uuid
from pathlib import Path
from typing import Optional
from fastapi import HTTPException, UploadFile, status

from app.core.config import get_settings

logger = logging.getLogger("app.services.storage_service")


class StorageService:
    """Service class responsible for local file persistence and validation."""

    # Centralized upload configurations
    ALLOWED_MIME_TYPES = {
        "audio/mpeg",
        "audio/wav",
        "audio/x-wav",
        "audio/mp4",
    }
    
    ALLOWED_EXTENSIONS = {
        ".mp3",
        ".wav",
        ".m4a",
    }

    MAX_UPLOAD_SIZE = 104_857_600  # 100 MB in bytes

    @classmethod
    def validate_file_metadata(cls, upload_file: UploadFile) -> None:
        """
        Validates basic file metadata including MIME type, file extension, 
        and size headers. Throws HTTPException for invalid inputs.
        """
        # Validate MIME type
        if upload_file.content_type not in cls.ALLOWED_MIME_TYPES:
            logger.warning(
                "Upload rejected: Unsupported MIME type %s for file %s",
                upload_file.content_type,
                upload_file.filename,
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unsupported audio format. Allowed MIME types: MP3, WAV, MP4/M4A.",
            )

        # Validate file extension
        orig_filename = upload_file.filename or ""
        orig_ext = Path(orig_filename).suffix.lower()
        if orig_ext not in cls.ALLOWED_EXTENSIONS:
            logger.warning(
                "Upload rejected: Unsupported file extension %s for file %s",
                orig_ext,
                upload_file.filename,
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unsupported audio format. Allowed extensions: .mp3, .wav, .m4a.",
            )

        # Check metadata size (if present in request headers)
        if upload_file.size is not None and upload_file.size > cls.MAX_UPLOAD_SIZE:
            logger.warning(
                "Upload rejected: File size %s exceeds 100MB",
                upload_file.size,
            )
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="File size exceeds the maximum limit of 100 MB.",
            )

    @classmethod
    def generate_unique_filename(cls, original_filename: Optional[str]) -> str:
        """
        Generates a unique filename using a version 4 UUID, preserving the original extension.
        - Security Decision: We completely discard the original user-supplied filename when writing to disk.
          This neutralizes path traversal attacks (e.g. filename="../../etc/passwd") and prevents malicious
          overwrite of system files or file collisions on host filesystems.
        """
        orig_ext = Path(original_filename or "").suffix.lower()
        return f"{uuid.uuid4().hex}{orig_ext}"

    @classmethod
    async def stream_file_to_disk(cls, upload_file: UploadFile, destination_path: Path) -> int:
        """
        Streams uploaded file content chunks to disk and enforces MAX_UPLOAD_SIZE dynamically.
        Deletes the file and raises HTTPException if size is exceeded.
        """
        total_bytes = 0
        try:
            with open(destination_path, "wb") as buffer:
                while True:
                    # Memory Safety Decision: Read the file in 1MB chunks instead of loading the entire
                    # file into memory at once. This keeps the application's RAM footprint low and constant,
                    # protecting the API service from Out-Of-Memory (OOM) crashes under concurrent uploads.
                    chunk = await upload_file.read(1024 * 1024)
                    if not chunk:
                        break

                    # Enforce the maximum allowed file size dynamically at each step. This defends against
                    # clients bypassing header checks (e.g., sending false Content-Length headers) and prevents
                    # disk space exhaustion attacks (Denial of Service).
                    total_bytes += len(chunk)
                    if total_bytes > cls.MAX_UPLOAD_SIZE:
                        logger.warning(
                            "Upload aborted: Streamed bytes %d exceeded 100MB limit",
                            total_bytes,
                        )
                        # Close buffer and cleanup partial file to avoid leaving orphaned disk blocks
                        buffer.close()
                        if destination_path.exists():
                            destination_path.unlink()
                        raise HTTPException(
                            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                            detail="File size exceeds the maximum limit of 100 MB.",
                        )
                    buffer.write(chunk)
            return total_bytes
        except HTTPException:
            raise
        except Exception as e:
            logger.error(
                "Failed to write file to disk. Error: %s",
                str(e),
                exc_info=True,
            )
            if destination_path.exists():
                destination_path.unlink()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An error occurred while saving the uploaded file.",
            )

    @classmethod
    async def save_audio_file(cls, upload_file: UploadFile) -> str:
        """
        Validates content type, verifies file size constraints, generates a unique UUID name,
        safely extracts the original extension, and streams the file to disk chunk by chunk.
        
        Returns the string path where the file is persisted.
        """
        settings = get_settings()

        # 1. Validate file metadata (MIME, extension, header size)
        cls.validate_file_metadata(upload_file)

        # 2. Resolve destination directory and ensure it exists
        upload_dir = Path(settings.UPLOAD_DIRECTORY)
        upload_dir.mkdir(parents=True, exist_ok=True)

        # 3. Generate unique UUID filename preserving original extension
        unique_filename = cls.generate_unique_filename(upload_file.filename)
        destination_path = upload_dir / unique_filename

        # 4. Stream chunks and enforce size limits dynamically
        await cls.stream_file_to_disk(upload_file, destination_path)

        return str(destination_path)
