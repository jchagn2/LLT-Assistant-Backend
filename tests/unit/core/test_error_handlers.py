"""
Unit tests for error handlers and middleware.

Tests custom exceptions, global exception handlers, and request ID middleware.
"""

import uuid
from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

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
from app.core.middleware import RequestIDMiddleware, register_exception_handlers


class TestCustomExceptions:
    """Test custom exception classes."""

    def test_llt_exception_base(self):
        """Test LLTException base class."""
        exc = LLTException(
            message="Test error",
            error_code="TEST_ERROR",
            details={"key": "value"},
        )

        assert str(exc) == "Test error"
        assert exc.error_code == "TEST_ERROR"
        assert exc.details == {"key": "value"}

    def test_project_already_exists_error(self):
        """Test ProjectAlreadyExistsError."""
        exc = ProjectAlreadyExistsError("test-project")

        assert "test-project" in str(exc)
        assert exc.error_code == "PROJECT_EXISTS"
        assert exc.details["project_id"] == "test-project"

    def test_project_not_found_error(self):
        """Test ProjectNotFoundError."""
        exc = ProjectNotFoundError("missing-project")

        assert "missing-project" in str(exc)
        assert exc.error_code == "PROJECT_NOT_FOUND"
        assert exc.details["project_id"] == "missing-project"

    def test_version_conflict_error(self):
        """Test VersionConflictError."""
        exc = VersionConflictError(expected=5, received=3, project_id="test-project")

        assert "5" in str(exc)
        assert "3" in str(exc)
        assert exc.error_code == "VERSION_CONFLICT"
        assert exc.details["expected"] == 5
        assert exc.details["received"] == 3
        assert exc.details["project_id"] == "test-project"

    def test_version_conflict_error_without_project_id(self):
        """Test VersionConflictError without project_id."""
        exc = VersionConflictError(expected=2, received=1)

        assert exc.details["expected"] == 2
        assert exc.details["received"] == 1
        assert "project_id" not in exc.details

    def test_neo4j_connection_error(self):
        """Test Neo4jConnectionError."""
        exc = Neo4jConnectionError("Connection timeout")

        assert exc.error_code == "DB_CONNECTION_ERROR"
        assert exc.details["reason"] == "Connection timeout"

    def test_neo4j_query_error(self):
        """Test Neo4jQueryError."""
        long_query = "MATCH (n) " * 50  # Very long query
        exc = Neo4jQueryError(query=long_query, error="Syntax error")

        assert exc.error_code == "DB_QUERY_ERROR"
        assert len(exc.details["query"]) <= 103  # Truncated to 100 + "..."
        assert exc.details["error"] == "Syntax error"

    def test_validation_error(self):
        """Test ValidationError."""
        exc = ValidationError(field="project_id", reason="Cannot be empty")

        assert "project_id" in str(exc)
        assert exc.error_code == "VALIDATION_ERROR"
        assert exc.details["field"] == "project_id"
        assert exc.details["reason"] == "Cannot be empty"

    def test_batch_operation_error(self):
        """Test BatchOperationError."""
        exc = BatchOperationError(total=100, succeeded=95, failed=5)

        assert "95" in str(exc)
        assert "100" in str(exc)
        assert exc.error_code == "BATCH_OPERATION_ERROR"
        assert exc.details["total"] == 100
        assert exc.details["succeeded"] == 95
        assert exc.details["failed"] == 5

    def test_empty_files_error(self):
        """Test EmptyFilesError initialization and properties."""
        exc = EmptyFilesError()

        assert "cannot be empty" in str(exc).lower()
        assert exc.error_code == "EMPTY_FILES"
        assert exc.details["files_count"] == 0

    def test_no_symbols_error(self):
        """Test NoSymbolsError with file count."""
        exc = NoSymbolsError(total_files=5)

        assert "no symbols" in str(exc).lower()
        assert exc.error_code == "NO_SYMBOLS"
        assert exc.details["total_files"] == 5
        assert exc.details["files_with_symbols"] == 0


class TestRequestIDMiddleware:
    """Test RequestIDMiddleware."""

    def test_request_id_added_to_request(self):
        """Test that request ID is added to request state."""
        app = FastAPI()

        @app.get("/test")
        async def test_endpoint(request: Request):
            return {"request_id": request.state.request_id}

        app.add_middleware(RequestIDMiddleware)
        client = TestClient(app)

        response = client.get("/test")

        assert response.status_code == 200
        data = response.json()
        assert "request_id" in data
        # Validate it's a UUID
        uuid.UUID(data["request_id"])

    def test_request_id_in_response_header(self):
        """Test that request ID is in response headers."""
        app = FastAPI()

        @app.get("/test")
        async def test_endpoint():
            return {"status": "ok"}

        app.add_middleware(RequestIDMiddleware)
        client = TestClient(app)

        response = client.get("/test")

        assert "X-Request-ID" in response.headers
        # Validate it's a UUID
        uuid.UUID(response.headers["X-Request-ID"])


class TestExceptionHandlers:
    """Test global exception handlers."""

    def test_project_not_found_handler(self):
        """Test ProjectNotFoundError handler."""
        app = FastAPI()

        @app.get("/test")
        async def test_endpoint():
            raise ProjectNotFoundError("test-project")

        register_exception_handlers(app)
        app.add_middleware(RequestIDMiddleware)
        client = TestClient(app)

        response = client.get("/test")

        assert response.status_code == 404
        data = response.json()
        assert data["error_code"] == "PROJECT_NOT_FOUND"
        assert "test-project" in data["error"]
        assert "request_id" in data

    def test_project_exists_handler(self):
        """Test ProjectAlreadyExistsError handler."""
        app = FastAPI()

        @app.get("/test")
        async def test_endpoint():
            raise ProjectAlreadyExistsError("existing-project")

        register_exception_handlers(app)
        app.add_middleware(RequestIDMiddleware)
        client = TestClient(app)

        response = client.get("/test")

        assert response.status_code == 409
        data = response.json()
        assert data["error_code"] == "PROJECT_EXISTS"
        assert "existing-project" in data["error"]

    def test_version_conflict_handler(self):
        """Test VersionConflictError handler."""
        app = FastAPI()

        @app.get("/test")
        async def test_endpoint():
            raise VersionConflictError(expected=5, received=3)

        register_exception_handlers(app)
        app.add_middleware(RequestIDMiddleware)
        client = TestClient(app)

        response = client.get("/test")

        assert response.status_code == 409
        data = response.json()
        assert data["error_code"] == "VERSION_CONFLICT"
        assert "suggestion" in data

    def test_validation_error_handler(self):
        """Test ValidationError handler."""
        app = FastAPI()

        @app.get("/test")
        async def test_endpoint():
            raise ValidationError(field="name", reason="Required")

        register_exception_handlers(app)
        app.add_middleware(RequestIDMiddleware)
        client = TestClient(app)

        response = client.get("/test")

        assert response.status_code == 422
        data = response.json()
        assert data["error_code"] == "VALIDATION_ERROR"

    def test_empty_files_error_handler(self):
        """Test EmptyFilesError handler."""
        app = FastAPI()

        @app.get("/test")
        async def test_endpoint():
            raise EmptyFilesError()

        register_exception_handlers(app)
        app.add_middleware(RequestIDMiddleware)
        client = TestClient(app)

        response = client.get("/test")

        assert response.status_code == 422
        data = response.json()
        assert data["error_code"] == "EMPTY_FILES"
        assert "cannot be empty" in data["error"].lower()
        assert "request_id" in data

    def test_no_symbols_error_handler(self):
        """Test NoSymbolsError handler."""
        app = FastAPI()

        @app.get("/test")
        async def test_endpoint():
            raise NoSymbolsError(total_files=3)

        register_exception_handlers(app)
        app.add_middleware(RequestIDMiddleware)
        client = TestClient(app)

        response = client.get("/test")

        assert response.status_code == 422
        data = response.json()
        assert data["error_code"] == "NO_SYMBOLS"
        assert "no symbols" in data["error"].lower()
        assert data["details"]["total_files"] == 3
        assert "request_id" in data

    def test_neo4j_connection_error_handler(self):
        """Test Neo4jConnectionError handler."""
        app = FastAPI()

        @app.get("/test")
        async def test_endpoint():
            raise Neo4jConnectionError("Connection failed")

        register_exception_handlers(app)
        app.add_middleware(RequestIDMiddleware)
        client = TestClient(app)

        response = client.get("/test")

        assert response.status_code == 503
        data = response.json()
        assert data["error_code"] == "DB_CONNECTION_ERROR"
        assert "suggestion" in data

    def test_neo4j_query_error_handler(self):
        """Test Neo4jQueryError handler."""
        app = FastAPI()

        @app.get("/test")
        async def test_endpoint():
            raise Neo4jQueryError(query="MATCH (n)", error="Syntax error")

        register_exception_handlers(app)
        app.add_middleware(RequestIDMiddleware)
        client = TestClient(app)

        response = client.get("/test")

        assert response.status_code == 500
        data = response.json()
        assert data["error_code"] == "DB_QUERY_ERROR"

    def test_batch_operation_error_handler(self):
        """Test BatchOperationError handler."""
        app = FastAPI()

        @app.get("/test")
        async def test_endpoint():
            raise BatchOperationError(total=100, succeeded=95, failed=5)

        register_exception_handlers(app)
        app.add_middleware(RequestIDMiddleware)
        client = TestClient(app)

        response = client.get("/test")

        assert response.status_code == 207
        data = response.json()
        assert data["error_code"] == "BATCH_OPERATION_ERROR"
        assert data["details"]["succeeded"] == 95

    def test_generic_llt_exception_handler(self):
        """Test generic LLTException handler."""
        app = FastAPI()

        @app.get("/test")
        async def test_endpoint():
            raise LLTException(
                message="Custom error",
                error_code="CUSTOM_ERROR",
                details={"foo": "bar"},
            )

        register_exception_handlers(app)
        app.add_middleware(RequestIDMiddleware)
        client = TestClient(app)

        response = client.get("/test")

        assert response.status_code == 500
        data = response.json()
        assert data["error_code"] == "CUSTOM_ERROR"
        assert data["details"]["foo"] == "bar"

    def test_generic_exception_handler(self):
        """Test handler for unhandled exceptions."""
        app = FastAPI()

        @app.get("/test")
        async def test_endpoint():
            raise RuntimeError("Unexpected error")

        register_exception_handlers(app)
        app.add_middleware(RequestIDMiddleware)
        client = TestClient(app, raise_server_exceptions=False)

        response = client.get("/test")

        assert response.status_code == 500
        data = response.json()
        assert data["error_code"] == "INTERNAL_ERROR"
        assert "request_id" in data
