"""
FastAPI middleware and global exception handlers.

Provides:
- Request ID tracking middleware
- Global exception handlers for LLT custom exceptions
- Structured error responses
"""

import logging
import time
import uuid
from typing import Callable

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.error_handlers import (
    BatchOperationError,
    EmptyFilesError,
    LLTException,
    Neo4jConnectionError,
    Neo4jQueryError,
    NoSymbolsError,
    ProjectAlreadyExistsError,
    ProjectNotFoundError,
    ValidationError,
    VersionConflictError,
)

logger = logging.getLogger(__name__)


class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    Add unique request ID to each request.

    The request ID is:
    - Generated as UUID4
    - Attached to request.state.request_id
    - Included in response headers as X-Request-ID
    - Included in all log messages for request tracing
    """

    async def dispatch(self, request: Request, call_next: Callable):
        """
        Process request and add request ID with lifecycle logging.

        Args:
            request: Incoming request
            call_next: Next middleware/endpoint handler

        Returns:
            Response with X-Request-ID header
        """
        # Generate unique request ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        # Record start time for duration measurement
        start_time = time.time()

        # Log request start
        logger.info(
            "Request started",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "client_ip": request.client.host if request.client else None,
            },
        )

        # Process request - let exception handlers handle any exceptions
        response = await call_next(request)

        # Calculate duration
        duration_ms = int((time.time() - start_time) * 1000)

        # Log request completion with metrics
        logger.info(
            "Request completed",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": duration_ms,
            },
        )

        # Add request ID to response headers
        response.headers["X-Request-ID"] = request_id
        return response


def register_exception_handlers(app: FastAPI) -> None:
    """
    Register all custom exception handlers with FastAPI app.

    Args:
        app: FastAPI application instance
    """

    @app.exception_handler(ProjectNotFoundError)
    async def project_not_found_handler(
        request: Request, exc: ProjectNotFoundError
    ) -> JSONResponse:
        """Handle ProjectNotFoundError with 404 response."""
        request_id = getattr(request.state, "request_id", "unknown")

        logger.warning(
            "Project not found",
            extra={
                "request_id": request_id,
                "error_code": exc.error_code,
                "details": exc.details,
            },
        )

        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "error": exc.message,
                "error_code": exc.error_code,
                "details": exc.details,
                "request_id": request_id,
            },
        )

    @app.exception_handler(ProjectAlreadyExistsError)
    async def project_exists_handler(
        request: Request, exc: ProjectAlreadyExistsError
    ) -> JSONResponse:
        """Handle ProjectAlreadyExistsError with 409 response."""
        request_id = getattr(request.state, "request_id", "unknown")

        logger.warning(
            "Project already exists",
            extra={
                "request_id": request_id,
                "error_code": exc.error_code,
                "details": exc.details,
            },
        )

        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={
                "error": exc.message,
                "error_code": exc.error_code,
                "details": exc.details,
                "request_id": request_id,
            },
        )

    @app.exception_handler(VersionConflictError)
    async def version_conflict_handler(
        request: Request, exc: VersionConflictError
    ) -> JSONResponse:
        """Handle VersionConflictError with 409 response."""
        request_id = getattr(request.state, "request_id", "unknown")

        logger.warning(
            "Version conflict detected",
            extra={
                "request_id": request_id,
                "error_code": exc.error_code,
                "details": exc.details,
            },
        )

        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={
                "error": exc.message,
                "error_code": exc.error_code,
                "details": exc.details,
                "request_id": request_id,
                "suggestion": "Fetch latest version and retry",
            },
        )

    @app.exception_handler(ValidationError)
    async def validation_error_handler(
        request: Request, exc: ValidationError
    ) -> JSONResponse:
        """Handle ValidationError with 422 response."""
        request_id = getattr(request.state, "request_id", "unknown")

        logger.warning(
            "Validation error",
            extra={
                "request_id": request_id,
                "error_code": exc.error_code,
                "details": exc.details,
            },
        )

        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": exc.message,
                "error_code": exc.error_code,
                "details": exc.details,
                "request_id": request_id,
            },
        )

    @app.exception_handler(EmptyFilesError)
    async def empty_files_error_handler(
        request: Request, exc: EmptyFilesError
    ) -> JSONResponse:
        """Handle EmptyFilesError with 422 response."""
        request_id = getattr(request.state, "request_id", "unknown")

        logger.warning(
            "Empty files array validation error",
            extra={
                "request_id": request_id,
                "error_code": exc.error_code,
                "details": exc.details,
            },
        )

        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": exc.message,
                "error_code": exc.error_code,
                "details": exc.details,
                "request_id": request_id,
            },
        )

    @app.exception_handler(NoSymbolsError)
    async def no_symbols_error_handler(
        request: Request, exc: NoSymbolsError
    ) -> JSONResponse:
        """Handle NoSymbolsError with 422 response."""
        request_id = getattr(request.state, "request_id", "unknown")

        logger.warning(
            "No symbols validation error",
            extra={
                "request_id": request_id,
                "error_code": exc.error_code,
                "details": exc.details,
            },
        )

        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": exc.message,
                "error_code": exc.error_code,
                "details": exc.details,
                "request_id": request_id,
            },
        )

    @app.exception_handler(Neo4jConnectionError)
    async def neo4j_connection_error_handler(
        request: Request, exc: Neo4jConnectionError
    ) -> JSONResponse:
        """Handle Neo4jConnectionError with 503 response."""
        request_id = getattr(request.state, "request_id", "unknown")

        logger.error(
            "Neo4j connection error",
            extra={
                "request_id": request_id,
                "error_code": exc.error_code,
                "details": exc.details,
            },
        )

        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "error": "Service temporarily unavailable",
                "error_code": exc.error_code,
                "request_id": request_id,
                "suggestion": "Please try again later",
            },
        )

    @app.exception_handler(Neo4jQueryError)
    async def neo4j_query_error_handler(
        request: Request, exc: Neo4jQueryError
    ) -> JSONResponse:
        """Handle Neo4jQueryError with 500 response."""
        request_id = getattr(request.state, "request_id", "unknown")

        logger.error(
            "Neo4j query error",
            extra={
                "request_id": request_id,
                "error_code": exc.error_code,
                "details": exc.details,
            },
        )

        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "Database query failed",
                "error_code": exc.error_code,
                "request_id": request_id,
            },
        )

    @app.exception_handler(BatchOperationError)
    async def batch_operation_error_handler(
        request: Request, exc: BatchOperationError
    ) -> JSONResponse:
        """Handle BatchOperationError with 207 Multi-Status response."""
        request_id = getattr(request.state, "request_id", "unknown")

        logger.warning(
            "Batch operation partially failed",
            extra={
                "request_id": request_id,
                "error_code": exc.error_code,
                "details": exc.details,
            },
        )

        return JSONResponse(
            status_code=status.HTTP_207_MULTI_STATUS,
            content={
                "error": exc.message,
                "error_code": exc.error_code,
                "details": exc.details,
                "request_id": request_id,
            },
        )

    @app.exception_handler(LLTException)
    async def llt_exception_handler(
        request: Request, exc: LLTException
    ) -> JSONResponse:
        """Handle generic LLTException with 500 response."""
        request_id = getattr(request.state, "request_id", "unknown")

        logger.error(
            "LLT exception",
            extra={
                "request_id": request_id,
                "error_code": exc.error_code,
                "details": exc.details,
            },
        )

        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": exc.message,
                "error_code": exc.error_code,
                "details": exc.details,
                "request_id": request_id,
            },
        )

    @app.exception_handler(Exception)
    async def generic_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        """Handle all unhandled exceptions with 500 response."""
        request_id = getattr(request.state, "request_id", "unknown")

        logger.error(
            "Unhandled exception",
            extra={"request_id": request_id, "exception_type": type(exc).__name__},
            exc_info=True,
        )

        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "Internal server error",
                "error_code": "INTERNAL_ERROR",
                "request_id": request_id,
            },
        )
