"""Unit tests for Feature 1 (test generation) API contracts.

These tests focus on the request/response shapes for:
- POST /workflows/generate-tests
- GET  /tasks/{task_id}

The goal is to keep them aligned with docs/api/openapi.yaml.
"""

from datetime import datetime, timezone
from typing import Any, Dict

import pytest
from fastapi.testclient import TestClient

import app.api.v1.routes as routes_module
from app.main import app


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class TestGenerateTestsWorkflow:
    """Tests for /workflows/generate-tests endpoint."""

    def test_generate_tests_accepts_new_schema_and_returns_async_job_response(
        self, client: TestClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """POST /workflows/generate-tests uses new schema and AsyncJobResponse."""

        async def fake_create_task(payload: Dict[str, Any]) -> str:  # type: ignore[override]
            # Ensure payload already follows the new flattened schema
            assert "source_code" in payload
            assert isinstance(payload["source_code"], str)
            # Optional fields should not be required
            assert "existing_test_code" in payload
            return "123e4567-e89b-12d3-a456-426614174000"

        async def fake_execute_generate_tests_task(  # type: ignore[override]
            task_id: str, payload: Dict[str, Any]
        ) -> None:
            # No-op in unit test – background execution is tested elsewhere
            return None

        monkeypatch.setattr(routes_module, "create_task", fake_create_task)
        monkeypatch.setattr(
            routes_module,
            "execute_generate_tests_task",
            fake_execute_generate_tests_task,
        )

        payload = {
            "source_code": "def add(a, b): return a + b",
            "user_description": "Generate tests for simple addition",
            "existing_test_code": "def test_add(): assert add(1, 2) == 3",
            "context": {
                "mode": "new",
                "target_function": "add",
            },
        }

        response = client.post("/workflows/generate-tests", json=payload)

        assert response.status_code == 202
        data = response.json()

        # AsyncJobResponse contract from OpenAPI:
        # - task_id: string (uuid)
        # - status: one of [pending, processing]
        assert "task_id" in data
        assert data["task_id"] == "123e4567-e89b-12d3-a456-426614174000"

        assert "status" in data
        assert data["status"] in {"pending", "processing"}

        # estimated_time_seconds is optional in the spec, only check type when present
        if (
            "estimated_time_seconds" in data
            and data["estimated_time_seconds"] is not None
        ):
            assert isinstance(data["estimated_time_seconds"], int)

    def test_generate_tests_missing_source_code_is_rejected(
        self, client: TestClient
    ) -> None:
        """Requests without required source_code should fail validation."""

        payload = {
            # "source_code" is intentionally omitted
            "user_description": "Should be rejected",
        }

        response = client.post("/workflows/generate-tests", json=payload)

        # Depending on implementation this may be 400 (BadRequest) or 422 (validation error)
        assert response.status_code in {400, 422}


class TestTaskStatusEndpoint:
    """Tests for /tasks/{task_id} endpoint."""

    def test_get_task_status_returns_task_status_response_with_generate_tests_result(
        self, client: TestClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Successful task lookup returns TaskStatusResponse with GenerateTestsResult."""

        async def fake_get_task(task_id: str) -> Dict[str, Any]:  # type: ignore[override]
            assert task_id == "123e4567-e89b-12d3-a456-426614174000"
            return {
                "id": task_id,
                "status": "completed",
                "created_at": _iso_now(),
                "updated_at": _iso_now(),
                "result": {
                    "generated_code": "def test_add(): assert add(1, 2) == 3",
                    "explanation": "Covers basic happy-path addition.",
                },
                "error": None,
            }

        monkeypatch.setattr(routes_module, "get_task", fake_get_task)

        response = client.get(
            "/tasks/123e4567-e89b-12d3-a456-426614174000",
        )

        assert response.status_code == 200
        data = response.json()

        # TaskStatusResponse contract from OpenAPI:
        # - task_id: string (uuid)
        # - status: [pending, processing, completed, failed]
        # - created_at: date-time
        # - result: object (GenerateTestsResult for Feature 1)
        assert data["task_id"] == "123e4567-e89b-12d3-a456-426614174000"
        assert data["status"] == "completed"

        assert "created_at" in data
        assert isinstance(data["created_at"], str)

        result = data.get("result")
        assert isinstance(result, dict)
        assert result.get("generated_code")
        assert isinstance(result["generated_code"], str)
        assert result.get("explanation")
        assert isinstance(result["explanation"], str)

        # For a successful task, error should be null or absent
        if "error" in data:
            assert data["error"] is None

    def test_get_task_status_returns_404_when_task_not_found(
        self, client: TestClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Missing task should result in 404 with empty body according to the spec."""

        async def fake_get_task(task_id: str) -> None:  # type: ignore[override]
            return None

        monkeypatch.setattr(routes_module, "get_task", fake_get_task)

        response = client.get(
            "/tasks/00000000-0000-0000-0000-000000000000",
        )

        assert response.status_code == 404
        # According to OpenAPI spec, 404 response should have empty body
        assert response.content == b""

    def test_get_task_status_excludes_null_fields_for_pending_status(
        self, client: TestClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Pending tasks should not include result or error fields to avoid null values."""

        async def fake_get_task(task_id: str) -> dict:  # type: ignore[override]
            return {
                "id": task_id,
                "status": "pending",
                "created_at": "2025-11-26T10:00:00Z",
                "result": None,
                "error": None,
            }

        monkeypatch.setattr(routes_module, "get_task", fake_get_task)

        response = client.get("/tasks/123e4567-e89b-12d3-a456-426614174000")

        assert response.status_code == 200
        data = response.json()

        # Verify required fields are present
        assert data["task_id"] == "123e4567-e89b-12d3-a456-426614174000"
        assert data["status"] == "pending"
        assert data["created_at"] == "2025-11-26T10:00:00Z"

        # CRITICAL: result and error fields should NOT be present (not even as null)
        assert (
            "result" not in data
        ), "result field should be excluded for pending status"
        assert "error" not in data, "error field should be excluded for pending status"

    def test_get_task_status_excludes_null_fields_for_processing_status(
        self, client: TestClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Processing tasks should not include result or error fields to avoid null values."""

        async def fake_get_task(task_id: str) -> dict:  # type: ignore[override]
            return {
                "id": task_id,
                "status": "processing",
                "created_at": "2025-11-26T10:00:00Z",
                "result": None,
                "error": None,
            }

        monkeypatch.setattr(routes_module, "get_task", fake_get_task)

        response = client.get("/tasks/123e4567-e89b-12d3-a456-426614174000")

        assert response.status_code == 200
        data = response.json()

        # Verify required fields are present
        assert data["task_id"] == "123e4567-e89b-12d3-a456-426614174000"
        assert data["status"] == "processing"
        assert data["created_at"] == "2025-11-26T10:00:00Z"

        # CRITICAL: result and error fields should NOT be present (not even as null)
        assert (
            "result" not in data
        ), "result field should be excluded for processing status"
        assert (
            "error" not in data
        ), "error field should be excluded for processing status"


class TestAsyncTaskErrorHandling:
    """Test suite for async task error handling (Feature 1).

    These tests verify the fix for the "Crash-on-Error" bug where
    the service would crash when polling for failed task status.
    """

    def test_failed_task_returns_structured_error_not_string(
        self, client: TestClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """
        CRITICAL FIX: Verify failed tasks return structured error dict, not string.

        This test ensures that when async tasks fail, the error is properly
        stored as a structured dict matching TaskError schema, preventing
        Pydantic ValidationError that would crash the service.

        Regression test for: "Crash-on-Error" bug
        """

        async def fake_get_task(task_id: str) -> dict:  # type: ignore[override]
            # Simulate what Redis now stores after the fix:
            # Error is a dict matching TaskError schema
            return {
                "id": task_id,
                "status": "failed",
                "created_at": "2025-11-26T10:00:00Z",
                "result": None,
                "error": {
                    "message": "Simulating a backend error for test",
                    "code": None,
                    "details": None,
                },
            }

        monkeypatch.setattr(routes_module, "get_task", fake_get_task)

        response = client.get("/tasks/123e4567-e89b-12d3-a456-426614174000")

        # Service must NOT crash - always return 200
        assert (
            response.status_code == 200
        ), "GET /tasks/{id} should not crash when task has structured error"

        data = response.json()
        assert data["task_id"] == "123e4567-e89b-12d3-a456-426614174000"
        assert data["status"] == "failed"
        assert data["created_at"] == "2025-11-26T10:00:00Z"

        # Verify error is structured object, not string
        assert "error" in data, "Response should contain 'error' field for failed tasks"
        assert isinstance(
            data["error"], dict
        ), "Error should be a structured dict, not string (fix for crash bug)"
        assert "message" in data["error"], "Error dict should contain 'message' field"
        assert (
            data["error"]["message"] == "Simulating a backend error for test"
        ), "Error message should match stored value"
        assert "code" in data["error"], "Error dict should contain 'code' field"
        assert (
            data["error"]["code"] is None
        ), "Error code should be None for generic errors"
        assert "details" in data["error"], "Error dict should contain 'details' field"

        # Verify result field is not present (only error for failed tasks)
        assert "result" not in data, "result field should be excluded for failed status"

    def test_failed_task_handles_legacy_string_error_gracefully(
        self, client: TestClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """
        Verify backward compatibility: handle legacy string errors without crashing.

        If old string errors exist in Redis from before the fix,
        the route handler should gracefully convert them to TaskError objects.
        """

        async def fake_get_task(task_id: str) -> dict:  # type: ignore[override]
            # Simulate legacy format: error stored as plain string
            return {
                "id": task_id,
                "status": "failed",
                "created_at": "2025-11-26T10:00:00Z",
                "result": None,
                "error": "Legacy string error message",  # Old format
            }

        monkeypatch.setattr(routes_module, "get_task", fake_get_task)

        response = client.get("/tasks/123e4567-e89b-12d3-a456-426614174000")

        # Should handle legacy format gracefully
        assert (
            response.status_code == 200
        ), "Should handle legacy string errors without crashing"

        data = response.json()
        assert data["status"] == "failed"

        # Verify error is converted to structured format
        assert isinstance(
            data["error"], dict
        ), "Legacy string error should be converted to dict"
        assert (
            data["error"]["message"] == "Legacy string error message"
        ), "Legacy error message should be preserved"
        assert data["error"]["code"] is None
        assert data["error"]["details"] is None
