from functools import lru_cache
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    """
    Application settings container utilizing Pydantic Settings v2.
    Loads variables from system environment and optionally falls back to .env files.
    """
    model_config = SettingsConfigDict(
        env_file=(".env", "backend/.env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

    DATABASE_URL: str = Field(
        default="postgresql://postgres:postgrespassword@localhost:5432/meeting_agent",
        description="PostgreSQL connection string"
    )

    # Database connection pool configurations
    DB_POOL_SIZE: int = Field(
        default=10, 
        description="The number of connections to keep open inside the connection pool"
    )
    DB_MAX_OVERFLOW: int = Field(
        default=20, 
        description="The number of connections to allow in the connection pool past pool_size"
    )
    DB_POOL_TIMEOUT: int = Field(
        default=30, 
        description="The number of seconds to wait before giving up on getting a connection from the pool"
    )
    DB_POOL_RECYCLE: int = Field(
        default=1800, 
        description="Recycle connections older than this threshold (in seconds)"
    )
    DB_POOL_PRE_PING: bool = Field(
        default=True,
        description="Verify connection health on checkout (pre-ping)"
    )

    # File Storage configurations
    UPLOAD_DIRECTORY: str = Field(
        default="uploads/meetings",
        description="Directory to store uploaded audio files"
    )

    # Celery retry configurations
    CELERY_MAX_RETRIES: int = Field(
        default=3,
        description="Max retries for Celery tasks"
    )
    CELERY_RETRY_BACKOFF: bool = Field(
        default=True,
        description="Enable Celery task retry backoff"
    )
    CELERY_RETRY_JITTER: bool = Field(
        default=True,
        description="Enable Celery task retry jitter"
    )

    # Whisper Speech-to-Text configurations
    WHISPER_MODEL_SIZE: str = Field(
        default="base",
        description="Faster-Whisper model size to use, e.g. tiny, base, small, medium, large-v3"
    )
    WHISPER_DEVICE: str = Field(
        default="cpu",
        description="Device to run inference on, e.g. cpu, cuda"
    )
    WHISPER_COMPUTE_TYPE: str = Field(
        default="int8",
        description="Compute type/quantization to use, e.g. float16, int8, int8_float16"
    )
    WHISPER_BEAM_SIZE: int = Field(
        default=5,
        description="Beam size for transcription decoding"
    )
    WHISPER_LANGUAGE: Optional[str] = Field(
        default=None,
        description="Specify default language for transcription. If None, auto-detected."
    )
    WHISPER_VAD_FILTER: bool = Field(
        default=True,
        description="Enable Voice Activity Detection (VAD) to filter out silences"
    )

    # Google Gemini configurations
    GEMINI_API_KEY: Optional[str] = Field(
        default=None,
        description="Google Gemini API key"
    )
    GEMINI_MODEL: str = Field(
        default="gemini-2.5-flash",
        description="Gemini model name to use"
    )
    GEMINI_TEMPERATURE: float = Field(
        default=0.2,
        description="Temperature for Gemini text generation"
    )
    GEMINI_MAX_OUTPUT_TOKENS: Optional[int] = Field(
        default=4096,
        description="Max output tokens for Gemini generation"
    )



    @property
    def ASYNC_DATABASE_URL(self) -> str:
        """
        Converts a standard PostgreSQL connection URL (postgresql:// or postgres://)
        into an asyncpg URL (postgresql+asyncpg://) for SQLAlchemy's AsyncEngine.
        """
        url = self.DATABASE_URL
        if url.startswith("postgresql://"):
            return url.replace("postgresql://", "postgresql+asyncpg://", 1)
        elif url.startswith("postgres://"):
            return url.replace("postgres://", "postgresql+asyncpg://", 1)
        return url

@lru_cache
def get_settings() -> Settings:
    """
    Returns a cached Settings instance using lru_cache.
    This prevents repeatedly reading environment variables and recreating the Settings object.
    """
    return Settings()

# Alias for simple importing
settings = get_settings()
