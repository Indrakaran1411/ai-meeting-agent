import logging
from typing import AsyncGenerator
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from app.core.config import get_settings

logger = logging.getLogger("app.db.database")

# Load settings using lru_cache
settings = get_settings()

# Create the asynchronous engine with optimized connection pooling
engine: AsyncEngine = create_async_engine(
    settings.ASYNC_DATABASE_URL,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    pool_timeout=settings.DB_POOL_TIMEOUT,
    pool_recycle=settings.DB_POOL_RECYCLE,
    pool_pre_ping=settings.DB_POOL_PRE_PING,  # Connection health check configured via Settings
    future=True,                               # Force SQLAlchemy 2.0-style execution APIs
)

# AsyncSession factory configured for resource optimization
async_session_maker = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,  # Prevent extra queries on accessing model attributes after commit
)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency yielding an AsyncSession.
    Guarantees session cleanup after request execution.
    """
    async with async_session_maker() as session:
        try:
            yield session
        except Exception as e:
            logger.error("Database session error: %s", e)
            raise
        finally:
            await session.close()
            logger.debug("Database session closed successfully")

async def check_database_connection() -> bool:
    """
    Asynchronously checks database connectivity by executing SELECT 1.
    Returns True if database responds successfully, False otherwise.
    """
    try:
        async with async_session_maker() as session:
            result = await session.execute(text("SELECT 1"))
            val = result.scalar()
            if val == 1:
                logger.info("Database connectivity check passed.")
                return True
            logger.warning("Database connectivity check returned unexpected result: %s", val)
            return False
    except Exception as e:
        logger.error("Database connectivity check failed: %s", e)
        return False
