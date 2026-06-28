from contextlib import asynccontextmanager
from fastapi import FastAPI, status
from app.api import api_v1_router, infrastructure_router
from app.core.exceptions import setup_exception_handlers
from app.core.logging_config import setup_logging, CorrelationIdMiddleware
from app.schemas.meeting import ErrorResponse

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Boot/startup phase completes, yield execution
    yield
    # Shutdown phase begins
    import logging
    shutdown_logger = logging.getLogger("app.shutdown")
    shutdown_logger.info("Lifespan shutdown: Cleaning up system resources...")

    # 1. Dispose of SQLAlchemy AsyncEngine connection pool
    try:
        from app.db.database import engine
        shutdown_logger.info("Lifespan shutdown: Disposing database engine...")
        await engine.dispose()
        shutdown_logger.info("Lifespan shutdown: Database engine disposed successfully.")
    except Exception as db_err:
        shutdown_logger.error("Lifespan shutdown: Error disposing database engine: %s", db_err)

    # 2. Close shared HTTP client inside WebhookService
    try:
        from app.services.webhook_service import WebhookService
        shutdown_logger.info("Lifespan shutdown: Closing WebhookService HTTP client...")
        await WebhookService.close_client()
        shutdown_logger.info("Lifespan shutdown: WebhookService HTTP client closed successfully.")
    except Exception as http_err:
        shutdown_logger.error("Lifespan shutdown: Error closing WebhookService HTTP client: %s", http_err)

# Configure logging before creating FastAPI app instance
setup_logging()

app = FastAPI(
    title="Meeting Intelligence Agent",
    description="Enterprise Meeting & Channel Intelligence Agent API",
    version="0.1.0",
    lifespan=lifespan,
)

# Register request correlation ID middleware
app.add_middleware(CorrelationIdMiddleware)

# Setup centralized exception handling
setup_exception_handlers(app)

# Register endpoints (infrastructure endpoints registered at root level)
app.include_router(infrastructure_router)
app.include_router(api_v1_router)


@app.get(
    "/",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Get root service status",
    description="Basic health status check returning service name and root response.",
    response_description="Root service health check information",
    tags=["Health"],
    responses={500: {"model": ErrorResponse, "description": "Internal Server Error"}}
)
async def health_check_root():
    return {"status": "ok", "service": "meeting-intelligence-agent"}


