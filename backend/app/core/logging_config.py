import contextvars
import logging
import time
import uuid
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

# ContextVar to store the current request ID
request_id_var: contextvars.ContextVar[str] = contextvars.ContextVar("request_id", default="-")

logger = logging.getLogger("app.request")


class CorrelationIdFormatter(logging.Formatter):
    """Custom logging formatter that injects request correlation IDs."""
    def format(self, record):
        record.request_id = request_id_var.get()
        return super().format(record)


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    """Middleware to assign request IDs and log requests with latency."""
    async def dispatch(self, request: Request, call_next) -> Response:
        # 1. Retrieve and validate correlation ID
        raw_correlation_id = request.headers.get("X-Request-ID")
        correlation_id = None
        
        if raw_correlation_id:
            cleaned = raw_correlation_id.strip()
            # Validation rules:
            # - Must not be empty
            # - Must not exceed 128 characters
            # - Must not contain newline or carriage return
            if (
                cleaned
                and len(cleaned) <= 128
                and "\n" not in cleaned
                and "\r" not in cleaned
            ):
                correlation_id = cleaned

        if not correlation_id:
            correlation_id = str(uuid.uuid4())
        
        # 2. Store correlation ID in ContextVar and request state
        token = request_id_var.set(correlation_id)
        request.state.request_id = correlation_id
        
        start_time = time.perf_counter()
        
        try:
            response = await call_next(request)
        except Exception as exc:
            elapsed_time_ms = (time.perf_counter() - start_time) * 1000
            logger.error(
                "Request failed: %s %s - Status 500 - %.2fms",
                request.method,
                request.url.path,
                elapsed_time_ms,
            )
            request_id_var.reset(token)
            raise exc
        
        elapsed_time_ms = (time.perf_counter() - start_time) * 1000
        
        # 3. Add Request ID header to response
        response.headers["X-Request-ID"] = correlation_id
        
        # 4. Log the HTTP request
        logger.info(
            "Request: %s %s - Status %d - %.2fms",
            request.method,
            request.url.path,
            response.status_code,
            elapsed_time_ms,
        )
        
        request_id_var.reset(token)
        return response


def setup_logging() -> None:
    """Configure centralized application logging."""
    log_format = (
        "[%(asctime)s] %(levelname)s [%(request_id)s] %(name)s: %(message)s"
    )
    
    # Configure root logger
    handler = logging.StreamHandler()
    handler.setFormatter(CorrelationIdFormatter(log_format))
    
    root_logger = logging.getLogger()
    for h in root_logger.handlers[:]:
        root_logger.removeHandler(h)
    root_logger.addHandler(handler)
    root_logger.setLevel(logging.INFO)

    # Apply formatting to uvicorn loggers
    for logger_name in ("uvicorn", "uvicorn.access", "uvicorn.error"):
        uv_logger = logging.getLogger(logger_name)
        # Clear existing handlers/formatters and set our stream handler
        for h in uv_logger.handlers[:]:
            uv_logger.removeHandler(h)
        uv_logger.addHandler(handler)
        uv_logger.propagate = False
