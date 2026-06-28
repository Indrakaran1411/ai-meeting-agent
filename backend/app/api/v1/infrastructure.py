import asyncio
import logging
import os
import redis.asyncio as aioredis
from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
from sqlalchemy import text
from app.db.database import async_session_maker

logger = logging.getLogger("app.infrastructure")

router = APIRouter(tags=["Infrastructure"])


@router.get("/health")
async def health_check():
    logger.info("Infrastructure: GET /health check requested.")
    return {
        "status": "healthy",
        "service": "meeting-agent",
        "version": "0.1.0"
    }


@router.get("/ready")
async def readiness_check():
    logger.info("Infrastructure: GET /ready check requested.")
    
    db_status = "ok"
    redis_status = "ok"
    
    # 1. Check database connectivity
    try:
        async with async_session_maker() as session:
            await session.execute(text("SELECT 1"))
    except Exception as exc:
        logger.error("Readiness check failed: database connectivity issue: %s", exc)
        db_status = "failed"
        
    # 2. Check Redis connectivity
    redis_url = os.environ.get("REDIS_URL", "redis://redis:6379/0")
    try:
        redis_client = aioredis.from_url(redis_url)
        # Use a short timeout of 2 seconds for ping to avoid hanging the check
        await asyncio.wait_for(redis_client.ping(), timeout=2.0)
        await redis_client.close()
    except Exception as exc:
        logger.error("Readiness check failed: redis connectivity issue: %s", exc)
        redis_status = "failed"
        
    is_ready = db_status == "ok" and redis_status == "ok"
    
    response_content = {
        "status": "ready" if is_ready else "not_ready",
        "database": db_status,
        "redis": redis_status
    }
    
    if is_ready:
        return response_content
    else:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content=response_content
        )
