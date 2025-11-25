"""
End-to-end integration tests for Phase 1 Context Management API.

These tests validate the complete request flow through the fully assembled
FastAPI application with real Neo4j database.

Requirements:
- Neo4j must be running (docker-compose up -d neo4j)
- Tests create and cleanup their own data
"""

import uuid

import pytest
from fastapi.testclient import TestClient

from app.core.graph.graph_service import GraphService
from app.main import app


@pytest.fixture
def test_project_id():
    """Generate unique project ID for each test."""
    return f"test-project-{uuid.uuid4().hex[:8]}"


@pytest.fixture
async def cleanup_project(test_project_id):
    """Cleanup project data after test."""
    yield
    # Cleanup after test
    service = GraphService()
    try:
        await service.connect()
        await service.client.execute_query(
            "MATCH (s:Symbol {project_id: $project_id}) DETACH DELETE s",
            {"project_id": test_project_id},
        )
        # Also delete project version metadata if exists
        await service.client.execute_query(
            "MATCH (p:ProjectVersion {project_id: $project_id}) DELETE p",
            {"project_id": test_project_id},
        )
    finally:
        await service.close()


@pytest.mark.integration
def test_initialize_project_full_flow(test_project_id, cleanup_project):
    """Test complete project initialization flow through main app."""
    client = TestClient(app)

    # Prepare request payload
    payload = {
        "project_id": test_project_id,
        "workspace_path": "/Users/dev/test-workspace",
        "language": "python",
        "files": [
            {
                "path": "/app/utils.py",
                "symbols": [
                    {
                        "name": "calculate_tax",
                        "kind": "function",
                        "signature": "(price: float) -> float",
                        "line_start": 10,
                        "line_end": 20,
                        "calls": ["get_tax_rate"],
                    },
                    {
                        "name": "get_tax_rate",
                        "kind": "function",
                        "signature": "(region: str) -> float",
                        "line_start": 25,
                        "line_end": 30,
                        "calls": [],
                    },
                ],
            },
            {
                "path": "/app/models.py",
                "symbols": [
                    {
                        "name": "Product",
                        "kind": "class",
                        "line_start": 5,
                        "line_end": 15,
                        "calls": [],
                    }
                ],
            },
        ],
    }

    # Send request
    response = client.post("/context/projects/initialize", json=payload)

    # Assertions
    assert (
        response.status_code == 201
    ), f"Expected 201, got {response.status_code}: {response.text}"
    data = response.json()

    assert data["project_id"] == test_project_id
    assert data["status"] == "initialized"
    assert data["indexed_files"] == 2
    assert data["indexed_symbols"] >= 3
    assert data["processing_time_ms"] > 0
    assert "X-Request-ID" in response.headers


@pytest.mark.integration
def test_incremental_update_full_flow(test_project_id, cleanup_project):
    """Test incremental update flow with version locking."""
    client = TestClient(app)

    # Step 1: Initialize project
    init_payload = {
        "project_id": test_project_id,
        "workspace_path": "/Users/dev/test-workspace",
        "language": "python",
        "files": [
            {
                "path": "/app/service.py",
                "symbols": [
                    {
                        "name": "process_data",
                        "kind": "function",
                        "line_start": 10,
                        "line_end": 20,
                        "calls": [],
                    }
                ],
            }
        ],
    }

    init_response = client.post("/context/projects/initialize", json=init_payload)
    assert init_response.status_code == 201

    # Step 2: Get current version
    status_response = client.get(f"/context/projects/{test_project_id}/status")
    assert status_response.status_code == 200
    current_version = status_response.json()["backend_version"]

    # Step 3: Apply incremental update
    update_payload = {
        "version": current_version,
        "changes": [
            {
                "action": "modified",
                "file_path": "/app/service.py",
                "symbols_changed": [
                    {
                        "action": "added",
                        "symbol": {
                            "name": "validate_data",
                            "kind": "function",
                            "line_start": 25,
                            "line_end": 30,
                            "calls": [],
                        },
                    }
                ],
            }
        ],
    }

    update_response = client.patch(
        f"/context/projects/{test_project_id}/incremental",
        json=update_payload,
    )

    # Assertions
    assert update_response.status_code == 200
    update_data = update_response.json()

    assert update_data["project_id"] == test_project_id
    assert update_data["version"] == current_version + 1
    assert update_data["changes_applied"] >= 1
    assert "updated_at" in update_data


@pytest.mark.integration
def test_project_status_full_flow(test_project_id, cleanup_project):
    """Test project status query."""
    client = TestClient(app)

    # Initialize project first
    init_payload = {
        "project_id": test_project_id,
        "workspace_path": "/Users/dev/test-workspace",
        "language": "python",
        "files": [
            {
                "path": "/app/main.py",
                "symbols": [
                    {
                        "name": "main",
                        "kind": "function",
                        "line_start": 1,
                        "line_end": 10,
                        "calls": [],
                    }
                ],
            }
        ],
    }

    init_response = client.post("/context/projects/initialize", json=init_payload)
    assert init_response.status_code == 201

    # Query status
    response = client.get(f"/context/projects/{test_project_id}/status")

    # Assertions
    assert response.status_code == 200
    data = response.json()

    assert data["project_id"] == test_project_id
    assert data["status"] == "active"
    assert data["indexed_files"] >= 1
    assert data["indexed_symbols"] >= 1
    assert data["backend_version"] >= 1
    assert "last_updated_at" in data


@pytest.mark.integration
def test_version_conflict_detection(test_project_id, cleanup_project):
    """Test that version conflicts are properly detected."""
    client = TestClient(app)

    # Initialize project
    init_payload = {
        "project_id": test_project_id,
        "workspace_path": "/Users/dev/test-workspace",
        "language": "python",
        "files": [
            {
                "path": "/app/test.py",
                "symbols": [
                    {
                        "name": "test_func",
                        "kind": "function",
                        "line_start": 1,
                        "line_end": 5,
                        "calls": [],
                    }
                ],
            }
        ],
    }

    client.post("/context/projects/initialize", json=init_payload)

    # Try to update with wrong version
    update_payload = {
        "version": 999,  # Wrong version
        "changes": [
            {
                "action": "modified",
                "file_path": "/app/test.py",
                "symbols_changed": [],
            }
        ],
    }

    response = client.patch(
        f"/context/projects/{test_project_id}/incremental",
        json=update_payload,
    )

    # Assertions
    assert response.status_code == 409
    data = response.json()
    assert "version" in data["error"].lower() or "conflict" in data["error"].lower()


@pytest.mark.integration
def test_project_not_found(test_project_id):
    """Test 404 response for non-existent project."""
    client = TestClient(app)

    # Query status for non-existent project
    response = client.get(f"/context/projects/nonexistent-{test_project_id}/status")

    # Assertions
    assert response.status_code == 404
    data = response.json()
    assert "error" in data
    assert "not found" in data["error"].lower()
    assert "request_id" in data


@pytest.mark.integration
def test_request_id_in_responses(test_project_id, cleanup_project):
    """Test that request IDs are present in all responses."""
    client = TestClient(app)

    # Test 1: Success response
    init_payload = {
        "project_id": test_project_id,
        "workspace_path": "/Users/dev/test-workspace",
        "language": "python",
        "files": [
            {
                "path": "/app/example.py",
                "symbols": [
                    {
                        "name": "example_func",
                        "kind": "function",
                        "line_start": 1,
                        "line_end": 5,
                        "calls": [],
                    }
                ],
            }
        ],
    }

    success_response = client.post("/context/projects/initialize", json=init_payload)
    assert "X-Request-ID" in success_response.headers
    request_id_1 = success_response.headers["X-Request-ID"]
    assert len(request_id_1) > 0

    # Test 2: Error response (duplicate project)
    error_response = client.post("/context/projects/initialize", json=init_payload)
    assert error_response.status_code == 409
    assert "X-Request-ID" in error_response.headers
    request_id_2 = error_response.headers["X-Request-ID"]
    assert len(request_id_2) > 0
    assert request_id_1 != request_id_2  # Different requests should have different IDs

    # Test 3: Request ID in error response body
    error_data = error_response.json()
    assert "request_id" in error_data


@pytest.mark.integration
def test_project_already_exists(test_project_id, cleanup_project):
    """Test that duplicate project initialization is rejected."""
    client = TestClient(app)

    payload = {
        "project_id": test_project_id,
        "workspace_path": "/Users/dev/test-workspace",
        "language": "python",
        "files": [
            {
                "path": "/app/file.py",
                "symbols": [
                    {
                        "name": "func",
                        "kind": "function",
                        "line_start": 1,
                        "line_end": 3,
                        "calls": [],
                    }
                ],
            }
        ],
    }

    # First initialization should succeed
    response1 = client.post("/context/projects/initialize", json=payload)
    assert response1.status_code == 201

    # Second initialization should fail with 409
    response2 = client.post("/context/projects/initialize", json=payload)
    assert response2.status_code == 409
    data = response2.json()
    assert test_project_id in data["error"]
    assert data["error_code"] == "PROJECT_EXISTS"


@pytest.mark.integration
def test_delete_project_full_flow(test_project_id):
    """Test complete project deletion flow."""
    client = TestClient(app)

    # Step 1: Initialize project
    init_payload = {
        "project_id": test_project_id,
        "workspace_path": "/Users/dev/test-workspace",
        "language": "python",
        "files": [
            {
                "path": "/app/calculator.py",
                "symbols": [
                    {
                        "name": "add",
                        "kind": "function",
                        "signature": "(a: int, b: int) -> int",
                        "line_start": 10,
                        "line_end": 15,
                        "calls": [],
                    },
                    {
                        "name": "subtract",
                        "kind": "function",
                        "signature": "(a: int, b: int) -> int",
                        "line_start": 20,
                        "line_end": 25,
                        "calls": [],
                    },
                ],
            },
            {
                "path": "/app/utils.py",
                "symbols": [
                    {
                        "name": "format_result",
                        "kind": "function",
                        "line_start": 5,
                        "line_end": 10,
                        "calls": [],
                    }
                ],
            },
        ],
    }

    init_response = client.post("/context/projects/initialize", json=init_payload)
    assert init_response.status_code == 201
    assert init_response.json()["indexed_symbols"] == 3

    # Step 2: Verify project exists
    status_response = client.get(f"/context/projects/{test_project_id}/status")
    assert status_response.status_code == 200
    assert status_response.json()["indexed_symbols"] == 3

    # Step 3: Delete project
    delete_response = client.delete(f"/context/projects/{test_project_id}")
    assert delete_response.status_code == 204
    assert delete_response.content == b""  # Empty body
    assert "X-Request-ID" in delete_response.headers

    # Step 4: Verify project no longer exists
    status_after_delete = client.get(f"/context/projects/{test_project_id}/status")
    assert status_after_delete.status_code == 404
    assert "not found" in status_after_delete.json()["error"].lower()

    # Step 5: Delete again (idempotent) should still return 204
    delete_again_response = client.delete(f"/context/projects/{test_project_id}")
    assert delete_again_response.status_code == 204
    assert delete_again_response.content == b""


@pytest.mark.integration
def test_empty_files_validation(test_project_id):
    """Test that empty files array returns 422 with EMPTY_FILES error."""
    client = TestClient(app)

    payload = {
        "project_id": test_project_id,
        "workspace_path": "/Users/dev/test-workspace",
        "language": "python",
        "files": [],  # Empty array
    }

    response = client.post("/context/projects/initialize", json=payload)

    assert response.status_code == 422
    data = response.json()
    assert data["error_code"] == "EMPTY_FILES"
    assert data["details"]["files_count"] == 0
    assert "request_id" in data


@pytest.mark.integration
def test_no_symbols_validation(test_project_id):
    """Test that files with no symbols return 422 with NO_SYMBOLS error."""
    client = TestClient(app)

    payload = {
        "project_id": test_project_id,
        "workspace_path": "/Users/dev/test-workspace",
        "language": "python",
        "files": [
            {"path": "/app/empty1.py", "symbols": []},
            {"path": "/app/empty2.py", "symbols": []},
        ],
    }

    response = client.post("/context/projects/initialize", json=payload)

    assert response.status_code == 422
    data = response.json()
    assert data["error_code"] == "NO_SYMBOLS"
    assert data["details"]["total_files"] == 2
    assert data["details"]["files_with_symbols"] == 0
    assert "request_id" in data
