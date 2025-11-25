"""
Unit tests for Context Management API endpoints.

Tests all three production endpoints using mocked GraphService.
"""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1.context import router
from app.core.middleware import register_exception_handlers
from app.models.context import (
    FileSymbols,
    IncrementalUpdateRequest,
    InitializeProjectRequest,
    SymbolInfo,
)

# Create test app
app = FastAPI()
register_exception_handlers(app)  # Register exception handlers
app.include_router(router)
client = TestClient(app)


@pytest.fixture
def mock_graph_service():
    """Create mocked GraphService."""
    service = MagicMock()
    service.connect = AsyncMock()
    service.close = AsyncMock()
    service.create_indexes = AsyncMock()
    service.check_project_exists = AsyncMock()
    service.batch_create_symbols_chunked = AsyncMock()
    service.create_call_relationships = AsyncMock()
    service.increment_project_version = AsyncMock()
    service.get_project_statistics = AsyncMock()
    service.get_project_version = AsyncMock()
    service.delete_file_symbols = AsyncMock()
    service.update_file_symbols = AsyncMock()
    service.delete_project = AsyncMock()
    service.get_project_data = AsyncMock()
    return service


class TestInitializeProjectEndpoint:
    """Test POST /context/projects/initialize."""

    def test_initialize_project_success(self, mock_graph_service):
        """Test successful project initialization."""
        # Setup mocks
        mock_graph_service.check_project_exists.return_value = False
        mock_graph_service.batch_create_symbols_chunked.return_value = 10
        mock_graph_service.create_call_relationships.return_value = 5
        mock_graph_service.increment_project_version.return_value = 1

        with patch("app.api.v1.context.GraphService", return_value=mock_graph_service):
            # Make request
            response = client.post(
                "/context/projects/initialize",
                json={
                    "project_id": "test-project",
                    "workspace_path": "/test/path",
                    "language": "python",
                    "files": [
                        {
                            "path": "test.py",
                            "symbols": [
                                {
                                    "name": "test_func",
                                    "kind": "function",
                                    "line_start": 1,
                                    "line_end": 5,
                                }
                            ],
                        }
                    ],
                },
            )

        assert response.status_code == 201
        data = response.json()
        assert data["project_id"] == "test-project"
        assert data["status"] == "initialized"
        assert data["indexed_files"] == 1
        assert data["indexed_symbols"] == 10
        assert "processing_time_ms" in data

    def test_initialize_project_already_exists(self, mock_graph_service):
        """Test initialization when project already exists."""
        mock_graph_service.check_project_exists.return_value = True

        with patch("app.api.v1.context.GraphService", return_value=mock_graph_service):
            response = client.post(
                "/context/projects/initialize",
                json={
                    "project_id": "existing-project",
                    "workspace_path": "/test/path",
                    "files": [{"path": "test.py", "symbols": []}],
                },
            )

        assert response.status_code == 409
        assert "already exists" in response.json()["detail"]

    def test_initialize_project_validation_error(self):
        """Test initialization with invalid request data."""
        response = client.post(
            "/context/projects/initialize",
            json={
                "project_id": "",  # Empty project_id (invalid)
                "workspace_path": "/test/path",
                "files": [],  # Empty files (invalid)
            },
        )

        assert response.status_code == 422

    def test_initialize_project_with_multiple_files(self, mock_graph_service):
        """Test initialization with multiple files."""
        mock_graph_service.check_project_exists.return_value = False
        mock_graph_service.batch_create_symbols_chunked.return_value = 50
        mock_graph_service.create_call_relationships.return_value = 30
        mock_graph_service.increment_project_version.return_value = 1

        with patch("app.api.v1.context.GraphService", return_value=mock_graph_service):
            response = client.post(
                "/context/projects/initialize",
                json={
                    "project_id": "multi-file-project",
                    "workspace_path": "/test/path",
                    "files": [
                        {
                            "path": "file1.py",
                            "symbols": [
                                {
                                    "name": "func1",
                                    "kind": "function",
                                    "line_start": 1,
                                    "line_end": 10,
                                }
                            ],
                        },
                        {
                            "path": "file2.py",
                            "symbols": [
                                {
                                    "name": "func2",
                                    "kind": "function",
                                    "line_start": 5,
                                    "line_end": 15,
                                }
                            ],
                        },
                    ],
                },
            )

        assert response.status_code == 201
        data = response.json()
        assert data["indexed_files"] == 2

    def test_initialize_empty_files_returns_422(self):
        """Test that empty files array returns 422 with EMPTY_FILES code."""
        response = client.post(
            "/context/projects/initialize",
            json={
                "project_id": "test-project",
                "workspace_path": "/test/path",
                "language": "python",
                "files": [],  # Empty array
            },
        )

        assert response.status_code == 422
        data = response.json()
        assert data["error_code"] == "EMPTY_FILES"
        assert data["details"]["files_count"] == 0

    def test_initialize_no_symbols_returns_422(self):
        """Test that files with no symbols returns 422 with NO_SYMBOLS code."""
        response = client.post(
            "/context/projects/initialize",
            json={
                "project_id": "test-project",
                "workspace_path": "/test/path",
                "language": "python",
                "files": [
                    {"path": "a.py", "symbols": []},
                    {"path": "b.py", "symbols": []},
                    {"path": "c.py", "symbols": []},
                ],
            },
        )

        assert response.status_code == 422
        data = response.json()
        assert data["error_code"] == "NO_SYMBOLS"
        assert data["details"]["total_files"] == 3
        assert data["details"]["files_with_symbols"] == 0


class TestIncrementalUpdateEndpoint:
    """Test PATCH /context/projects/{project_id}/incremental."""

    def test_incremental_update_success(self, mock_graph_service):
        """Test successful incremental update."""
        mock_graph_service.check_project_exists.return_value = True
        mock_graph_service.get_project_version.return_value = 2
        mock_graph_service.update_file_symbols.return_value = {
            "added": 1,
            "modified": 2,
            "deleted": 0,
        }
        mock_graph_service.increment_project_version.return_value = 3

        with patch("app.api.v1.context.GraphService", return_value=mock_graph_service):
            response = client.patch(
                "/context/projects/test-project/incremental",
                json={
                    "version": 2,
                    "changes": [
                        {
                            "file_path": "test.py",
                            "action": "modified",
                            "symbols_changed": [
                                {
                                    "action": "added",
                                    "name": "new_func",
                                    "new_data": {
                                        "name": "new_func",
                                        "kind": "function",
                                        "line_start": 10,
                                        "line_end": 20,
                                    },
                                }
                            ],
                        }
                    ],
                },
            )

        assert response.status_code == 200
        data = response.json()
        assert data["project_id"] == "test-project"
        assert data["version"] == 3
        assert data["changes_applied"] == 3

    def test_incremental_update_project_not_found(self, mock_graph_service):
        """Test update when project doesn't exist."""
        mock_graph_service.check_project_exists.return_value = False

        with patch("app.api.v1.context.GraphService", return_value=mock_graph_service):
            response = client.patch(
                "/context/projects/nonexistent/incremental",
                json={
                    "version": 1,
                    "changes": [
                        {
                            "file_path": "test.py",
                            "action": "modified",
                        }
                    ],
                },
            )

        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    def test_incremental_update_version_conflict(self, mock_graph_service):
        """Test update with version conflict."""
        mock_graph_service.check_project_exists.return_value = True
        mock_graph_service.get_project_version.return_value = 5  # Current is 5

        with patch("app.api.v1.context.GraphService", return_value=mock_graph_service):
            response = client.patch(
                "/context/projects/test-project/incremental",
                json={
                    "version": 3,  # Client thinks it's 3 (conflict!)
                    "changes": [
                        {
                            "file_path": "test.py",
                            "action": "modified",
                        }
                    ],
                },
            )

        assert response.status_code == 409
        assert "Version conflict" in response.json()["detail"]

    def test_incremental_update_file_deletion(self, mock_graph_service):
        """Test deleting a file."""
        mock_graph_service.check_project_exists.return_value = True
        mock_graph_service.get_project_version.return_value = 1
        mock_graph_service.delete_file_symbols.return_value = 5
        mock_graph_service.increment_project_version.return_value = 2

        with patch("app.api.v1.context.GraphService", return_value=mock_graph_service):
            response = client.patch(
                "/context/projects/test-project/incremental",
                json={
                    "version": 1,
                    "changes": [
                        {
                            "file_path": "old_file.py",
                            "action": "deleted",
                        }
                    ],
                },
            )

        assert response.status_code == 200
        data = response.json()
        assert data["changes_applied"] == 5


class TestProjectStatusEndpoint:
    """Test GET /context/projects/{project_id}/status."""

    def test_get_project_status_success(self, mock_graph_service):
        """Test successful status retrieval."""
        mock_graph_service.check_project_exists.return_value = True
        mock_graph_service.get_project_statistics.return_value = {
            "total_files": 10,
            "total_symbols": 50,
            "total_relationships": 75,
        }
        mock_graph_service.get_project_version.return_value = 3

        with patch("app.api.v1.context.GraphService", return_value=mock_graph_service):
            response = client.get("/context/projects/test-project/status")

        assert response.status_code == 200
        data = response.json()
        assert data["project_id"] == "test-project"
        assert data["status"] == "active"
        assert data["indexed_files"] == 10
        assert data["indexed_symbols"] == 50
        assert data["backend_version"] == 3
        assert "last_updated_at" in data

    def test_get_project_status_not_found(self, mock_graph_service):
        """Test status when project doesn't exist."""
        mock_graph_service.check_project_exists.return_value = False

        with patch("app.api.v1.context.GraphService", return_value=mock_graph_service):
            response = client.get("/context/projects/nonexistent/status")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"]


class TestGetProjectDataEndpoint:
    """Test GET /context/projects/{project_id}."""

    def test_get_project_data_success(self, mock_graph_service):
        """Test successful retrieval of complete project data."""
        mock_graph_service.get_project_data.return_value = {
            "project_id": "test-project",
            "version": 3,
            "workspace_path": "/Users/test/project",
            "files": [
                {
                    "path": "src/main.py",
                    "symbols": [
                        {
                            "name": "main",
                            "kind": "function",
                            "signature": "() -> None",
                            "line_start": 10,
                            "line_end": 20,
                            "calls": ["initialize", "run"],
                        }
                    ],
                },
                {
                    "path": "src/utils.py",
                    "symbols": [
                        {
                            "name": "helper",
                            "kind": "function",
                            "signature": "(x: int) -> int",
                            "line_start": 5,
                            "line_end": 8,
                            "calls": [],
                        }
                    ],
                },
            ],
        }

        with patch("app.api.v1.context.GraphService", return_value=mock_graph_service):
            response = client.get("/context/projects/test-project")

        assert response.status_code == 200
        data = response.json()
        assert data["project_id"] == "test-project"
        assert data["version"] == 3
        assert data["workspace_path"] == "/Users/test/project"
        assert len(data["files"]) == 2
        assert data["files"][0]["path"] == "src/main.py"
        assert len(data["files"][0]["symbols"]) == 1
        assert data["files"][0]["symbols"][0]["name"] == "main"

    def test_get_project_data_not_found(self, mock_graph_service):
        """Test retrieval when project doesn't exist."""
        from app.core.error_handlers import ProjectNotFoundError

        mock_graph_service.get_project_data.side_effect = ProjectNotFoundError(
            "nonexistent-project"
        )

        with patch("app.api.v1.context.GraphService", return_value=mock_graph_service):
            response = client.get("/context/projects/nonexistent-project")

        assert response.status_code == 404
        data = response.json()
        assert "error" in data
        assert "not found" in data["error"].lower()

    def test_get_project_data_database_error(self, mock_graph_service):
        """Test retrieval with database error returns 503."""
        mock_graph_service.get_project_data.side_effect = Exception(
            "Database connection lost"
        )

        with patch("app.api.v1.context.GraphService", return_value=mock_graph_service):
            response = client.get("/context/projects/test-project")

        assert response.status_code == 503
        assert "Failed to retrieve project data" in response.json()["detail"]


class TestHelperFunctions:
    """Test helper functions for data preparation."""

    def test_prepare_symbols_for_db(self):
        """Test symbol preparation adds qualified_name."""
        from app.api.v1.context import prepare_symbols_for_db

        symbols = [
            SymbolInfo(
                name="test_func",
                kind="function",
                line_start=1,
                line_end=5,
            )
        ]

        result = prepare_symbols_for_db("test.py", symbols)

        assert len(result) == 1
        assert result[0]["name"] == "test_func"
        assert result[0]["qualified_name"] == "test.py::test_func"
        assert result[0]["file_path"] == "test.py"

    def test_prepare_relationships(self):
        """Test relationship extraction from symbols."""
        from app.api.v1.context import prepare_relationships

        symbols = [
            SymbolInfo(
                name="caller",
                kind="function",
                line_start=10,
                line_end=20,
                calls=["callee1", "callee2"],
            )
        ]

        result = prepare_relationships("test.py", symbols)

        assert len(result) == 2
        assert result[0]["caller_qualified_name"] == "test.py::caller"
        assert result[0]["callee_qualified_name"] == "callee1"
        assert result[0]["line"] == 10


class TestDeleteProjectEndpoint:
    """Test DELETE /context/projects/{project_id}."""

    def test_delete_project_success(self, mock_graph_service):
        """Test successful project deletion with symbols."""
        mock_graph_service.delete_project.return_value = 42  # 42 symbols deleted

        with patch("app.api.v1.context.GraphService", return_value=mock_graph_service):
            response = client.delete("/context/projects/test-project")

        assert response.status_code == 204
        assert response.content == b""  # Empty response body
        mock_graph_service.delete_project.assert_called_once_with("test-project")

    def test_delete_project_idempotent(self, mock_graph_service):
        """Test deletion is idempotent when project doesn't exist."""
        mock_graph_service.delete_project.return_value = 0  # No symbols deleted

        with patch("app.api.v1.context.GraphService", return_value=mock_graph_service):
            response = client.delete("/context/projects/nonexistent-project")

        assert response.status_code == 204
        assert response.content == b""
        mock_graph_service.delete_project.assert_called_once_with("nonexistent-project")

    def test_delete_project_database_error(self, mock_graph_service):
        """Test deletion with database error returns 503."""
        mock_graph_service.delete_project.side_effect = Exception(
            "Database connection lost"
        )

        with patch("app.api.v1.context.GraphService", return_value=mock_graph_service):
            response = client.delete("/context/projects/test-project")

        assert response.status_code == 503
        data = response.json()
        assert "Database operation failed" in data["detail"]
