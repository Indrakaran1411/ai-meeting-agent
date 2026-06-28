import logging
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger("app.core.exceptions")


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handle FastAPI HTTPExceptions."""
    logger.warning(
        "HTTPException: status_code=%d, detail=%s, path=%s",
        exc.status_code,
        exc.detail,
        request.url.path,
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "type": "http_exception",
                "message": exc.detail,
                "status_code": exc.status_code,
            }
        },
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Handle validation errors."""
    errors = exc.errors()
    # Construct a friendly message summarizing validation errors
    if errors:
        loc_str = ".".join(str(x) for x in errors[0].get("loc", []))
        msg = f"Validation failed: {errors[0].get('msg')} at {loc_str}"
    else:
        msg = "Request validation failed."

    logger.warning(
        "Validation error: path=%s, errors=%s",
        request.url.path,
        errors,
    )
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": {
                "type": "validation_error",
                "message": msg,
                "status_code": status.HTTP_422_UNPROCESSABLE_ENTITY,
                "details": errors,
            }
        },
    )


async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError) -> JSONResponse:
    """Handle database errors without exposing details to the client."""
    logger.exception(
        "Database exception occurred on path %s",
        request.url.path,
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "type": "database_error",
                "message": "An internal database error occurred.",
                "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
            }
        },
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle all other unhandled exceptions."""
    logger.exception(
        "Unhandled exception occurred on path %s",
        request.url.path,
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "type": "internal_server_error",
                "message": "An unexpected error occurred.",
                "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
            }
        },
    )


def setup_exception_handlers(app) -> None:
    """Register exception handlers on the FastAPI app instance."""
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(SQLAlchemyError, sqlalchemy_exception_handler)
    app.add_exception_handler(Exception, generic_exception_handler)
