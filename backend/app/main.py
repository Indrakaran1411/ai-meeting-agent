from fastapi import FastAPI
from app.api import api_v1_router, infrastructure_router
from app.core.exceptions import setup_exception_handlers
from app.core.logging_config import setup_logging, CorrelationIdMiddleware

# Configure logging before creating FastAPI app instance
setup_logging()

app = FastAPI(
    title="Meeting Intelligence Agent",
    description="Enterprise Meeting & Channel Intelligence Agent API",
    version="0.1.0",
)

# Register request correlation ID middleware
app.add_middleware(CorrelationIdMiddleware)

# Setup centralized exception handling
setup_exception_handlers(app)

# Register endpoints (infrastructure endpoints registered at root level)
app.include_router(infrastructure_router)
app.include_router(api_v1_router)


@app.get("/", tags=["Health"])
async def health_check_root():
    return {"status": "ok", "service": "meeting-intelligence-agent"}


