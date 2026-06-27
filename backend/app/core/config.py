from functools import lru_cache
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
