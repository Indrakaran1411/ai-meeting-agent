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

# Load settings using lru_cache to prevent repetitive parsing of environment variables.
settings = get_settings()

# Create the asynchronous database engine with connection pooling optimized for high concurrency.
# - pool_size: Keeps a hot pool of idle connections ready to serve requests instantly.
# - max_overflow: Allows temporary spikes in database traffic without blocking threads.
# - pool_timeout: Avoids thread starvation by failing fast if connections are exhausted.
# - pool_recycle: Regularly recycles connections to prevent firewall timeouts or database-side idle terminations.
# - pool_pre_ping: Performs a "SELECT 1" on checkout. If a socket is dead (e.g. database restarted),
#   it is transparently discarded and replaced, preventing 500 errors on client requests.
# - future: Enforces SQLAlchemy 2.0-style execution conventions.
engine: AsyncEngine = create_async_engine(
    settings.ASYNC_DATABASE_URL,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    pool_timeout=settings.DB_POOL_TIMEOUT,
    pool_recycle=settings.DB_POOL_RECYCLE,
    pool_pre_ping=settings.DB_POOL_PRE_PING,
    future=True,
)

# AsyncSession factory configured for resource optimization.
# expire_on_commit=False is crucial for async workflows: it prevents SQLAlchemy from attempting
# lazy-loads on model attributes after a transaction commits, which would otherwise raise exceptions
# due to the lack of an active database context on those entities.
async_session_maker = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency yielding an AsyncSession.
    Guarantees session cleanup after request execution.
    - Yields a database session instance to the route handler context.
    - Automatically closes the session on handler completion or failure to prevent pool leaks.
    """
    async with async_session_maker() as session:
        try:
            yield session
        except Exception as e:
            logger.error("Database session error: %s", e)
            raise
        finally:
            # Explicit close acts as a safeguard. The async context manager also closes it automatically.
            await session.close()
            logger.debug("Database session closed successfully")

async def check_database_connection() -> bool:
    """
    Asynchronously checks database connectivity by executing SELECT 1.
    Used by the readiness endpoint to verify dependency health.
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

