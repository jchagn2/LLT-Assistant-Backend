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
from app.models.context import (
    FileSymbols,
    IncrementalUpdateRequest,
    InitializeProjectRequest,
    SymbolInfo,
)

# Create test app
app = FastAPI()
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
