"""Unit tests for Feature 3: Impact Analysis API.

These tests verify the /analysis/impact endpoint functionality
including success paths and error handling.
"""

from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.api.v1.schemas import ImpactAnalysisResponse, ImpactItem
from app.main import app


def create_mock_impact_analyzer_context(mock_response):
    """Create a mock context manager that yields a mock analyzer."""

    @asynccontextmanager
    async def mock_context(*args, **kwargs):
        mock_analyzer = AsyncMock()
        mock_analyzer.analyze_impact_async = AsyncMock(return_value=mock_response)
        yield mock_analyzer

    return mock_context


def test_analyze_impact_success():
    """Test successful impact analysis with valid request."""
    client = TestClient(app)

    # Mock request payload matching OpenAPI specification
    request_payload = {
        "project_context": {
            "files_changed": [
                {"path": "src/module.py", "change_type": "modified"},
                {"path": "src/utils.py", "change_type": "added"},
            ],
            "related_tests": ["tests/test_module.py", "tests/test_utils.py"],
        }
    }

    mock_response = ImpactAnalysisResponse(
        impacted_tests=[
            ImpactItem(
                test_path="tests/test_module.py",
                impact_score=0.8,
                severity="high",
                reasons=["Test file name matches changed file: src/module.py"],
            ),
            ImpactItem(
                test_path="tests/test_utils.py",
                impact_score=1.0,
                severity="high",
                reasons=["Test file was directly modified"],
            ),
        ],
        severity="high",
        suggested_action="run-all-tests",
    )

    # Patch the context manager
    with patch(
        "app.api.v1.routes.get_impact_analyzer_context",
        create_mock_impact_analyzer_context(mock_response),
    ):
        response = client.post("/analysis/impact", json=request_payload)

    # Verify response
    assert response.status_code == 200
    response_data = response.json()

    # Verify response structure matches OpenAPI spec
    assert "impacted_tests" in response_data
    assert "severity" in response_data
    assert "suggested_action" in response_data

    # Verify impacted tests
    assert len(response_data["impacted_tests"]) == 2
    assert response_data["impacted_tests"][0]["test_path"] == "tests/test_module.py"
    assert response_data["impacted_tests"][0]["impact_score"] == 0.8
    assert response_data["impacted_tests"][0]["severity"] == "high"
    assert response_data["impacted_tests"][0]["reasons"] is not None

    # Verify overall assessment
    assert response_data["severity"] == "high"
    assert response_data["suggested_action"] == "run-all-tests"


def test_analyze_impact_no_files_changed():
    """Test impact analysis fails when files_changed is empty."""
    client = TestClient(app)

    request_payload = {
        "project_context": {
            "files_changed": [],  # Empty - should trigger validation error
            "related_tests": ["tests/test_module.py"],
        }
    }

    response = client.post("/analysis/impact", json=request_payload)

    # Should return 400 for validation error
    assert response.status_code == 400
    response_data = response.json()
    assert "detail" in response_data
    assert (
        "files_changed" in response_data["detail"].lower()
        or "cannot be empty" in response_data["detail"].lower()
    )


def test_analyze_impact_missing_files_changed():
    """Test impact analysis fails when files_changed is missing."""
    client = TestClient(app)

    request_payload = {
        "project_context": {
            # Missing files_changed field
            "related_tests": ["tests/test_module.py"],
        }
    }

    response = client.post("/analysis/impact", json=request_payload)

    # Should return 422 for validation error (missing required field)
    assert response.status_code == 422


def test_analyze_impact_single_test_file():
    """Test impact analysis with single test file change."""
    client = TestClient(app)

    request_payload = {
        "project_context": {
            "files_changed": [
                {"path": "tests/test_example.py", "change_type": "modified"}
            ],
            "related_tests": ["tests/test_example.py"],
        }
    }

    mock_response = ImpactAnalysisResponse(
        impacted_tests=[
            ImpactItem(
                test_path="tests/test_example.py",
                impact_score=1.0,
                severity="high",
                reasons=["Test file was directly modified"],
            )
        ],
        severity="low",
        suggested_action="run-affected-tests",
    )

    with patch(
        "app.api.v1.routes.get_impact_analyzer_context",
        create_mock_impact_analyzer_context(mock_response),
    ):
        response = client.post("/analysis/impact", json=request_payload)

    assert response.status_code == 200
    response_data = response.json()

    assert len(response_data["impacted_tests"]) == 1
    assert response_data["impacted_tests"][0]["test_path"] == "tests/test_example.py"
    assert response_data["impacted_tests"][0]["severity"] == "high"
    assert response_data["severity"] == "low"
    assert response_data["suggested_action"] == "run-affected-tests"


def test_analyze_impact_no_matching_tests():
    """Test impact analysis when no tests are clearly impacted."""
    client = TestClient(app)

    request_payload = {
        "project_context": {
            "files_changed": [{"path": "src/unrelated.py", "change_type": "modified"}],
            "related_tests": ["tests/test_something.py"],
        }
    }

    mock_response = ImpactAnalysisResponse(
        impacted_tests=[
            ImpactItem(
                test_path="tests/test_something.py",
                impact_score=0.1,
                severity="low",
                reasons=["Test file in related tests but no clear connection"],
            )
        ],
        severity="low",
        suggested_action="run-affected-tests",
    )

    with patch(
        "app.api.v1.routes.get_impact_analyzer_context",
        create_mock_impact_analyzer_context(mock_response),
    ):
        response = client.post("/analysis/impact", json=request_payload)

    assert response.status_code == 200
    response_data = response.json()

    assert len(response_data["impacted_tests"]) == 1
    assert response_data["impacted_tests"][0]["severity"] == "low"
    assert response_data["severity"] == "low"
    assert response_data["suggested_action"] == "run-affected-tests"


def test_analyze_impact_no_related_tests():
    """Test impact analysis with no related tests provided."""
    client = TestClient(app)

    request_payload = {
        "project_context": {
            "files_changed": [{"path": "src/module.py", "change_type": "modified"}],
            "related_tests": [],  # No related tests
        }
    }

    mock_response = ImpactAnalysisResponse(
        impacted_tests=[],  # Empty since no related tests
        severity="none",
        suggested_action="no-action",
    )

    with patch(
        "app.api.v1.routes.get_impact_analyzer_context",
        create_mock_impact_analyzer_context(mock_response),
    ):
        response = client.post("/analysis/impact", json=request_payload)

    assert response.status_code == 200
    response_data = response.json()

    assert len(response_data["impacted_tests"]) == 0
    assert response_data["severity"] == "none"
    assert response_data["suggested_action"] == "no-action"


def test_analyze_impact_analyzer_exception():
    """Test impact analysis handles analyzer exceptions gracefully."""
    client = TestClient(app)

    request_payload = {
        "project_context": {
            "files_changed": [{"path": "src/module.py", "change_type": "modified"}],
            "related_tests": ["tests/test_module.py"],
        }
    }

    @asynccontextmanager
    async def mock_context_with_exception(*args, **kwargs):
        mock_analyzer = AsyncMock()
        mock_analyzer.analyze_impact_async = AsyncMock(
            side_effect=Exception("Analyzer error")
        )
        yield mock_analyzer

    with patch(
        "app.api.v1.routes.get_impact_analyzer_context",
        mock_context_with_exception,
    ):
        response = client.post("/analysis/impact", json=request_payload)

    # Should return 500 for internal error
    assert response.status_code == 500
    response_data = response.json()
    assert "detail" in response_data
    assert "internal error" in response_data["detail"].lower()


def test_analyze_impact_analyzer_initialization_failure():
    """Test impact analysis handles analyzer initialization failure."""
    client = TestClient(app)

    request_payload = {
        "project_context": {
            "files_changed": [{"path": "src/module.py", "change_type": "modified"}],
            "related_tests": ["tests/test_module.py"],
        }
    }

    # Mock the actual dependency injection function to raise an exception
    with patch(
        "app.api.v1.routes.RuleEngine", side_effect=Exception("Initialization failed")
    ):
        response = client.post("/analysis/impact", json=request_payload)

    # Should return 503 for service unavailable
    assert response.status_code == 503
    response_data = response.json()
    assert "detail" in response_data
    assert "failed to initialize" in response_data["detail"].lower()


def test_analyze_impact_response_schema_compliance():
    """Test that response matches OpenAPI schema specification."""
    client = TestClient(app)

    request_payload = {
        "project_context": {
            "files_changed": [{"path": "src/example.py", "change_type": "modified"}],
            "related_tests": ["tests/test_example.py"],
        }
    }

    mock_response = ImpactAnalysisResponse(
        impacted_tests=[
            ImpactItem(
                test_path="tests/test_example.py",
                impact_score=0.9,
                severity="high",
                reasons=["Direct match with changed file"],
            )
        ],
        severity="high",
        suggested_action="run-affected-tests",
    )

    with patch(
        "app.api.v1.routes.get_impact_analyzer_context",
        create_mock_impact_analyzer_context(mock_response),
    ):
        response = client.post("/analysis/impact", json=request_payload)

    assert response.status_code == 200
    response_data = response.json()

    # Verify response follows OpenAPI schema
    # Check required fields exist
    assert isinstance(response_data["impacted_tests"], list)
    assert isinstance(response_data["severity"], str)
    assert isinstance(response_data["suggested_action"], str)

    # Check enum values are valid (updated to include "informational")
    valid_severities = ["high", "medium", "low", "informational", "none"]
    valid_actions = ["run-all-tests", "run-affected-tests", "no-action"]

    assert response_data["severity"] in valid_severities
    assert response_data["suggested_action"] in valid_actions

    # Check impact items structure
    for item in response_data["impacted_tests"]:
        assert "test_path" in item
        assert "impact_score" in item
        assert "severity" in item
        assert item["severity"] in valid_severities
        assert isinstance(item["impact_score"], (int, float))
        assert 0.0 <= item["impact_score"] <= 1.0


def test_analyze_impact_non_functional_change_informational():
    """Test that non-functional changes return informational severity."""
    client = TestClient(app)

    # Git diff with only comment changes (non-functional)
    git_diff = """
diff --git a/src/utils.py b/src/utils.py
@@ -10,5 +10,6 @@ def helper(x):
+    # Added documentation comment
     return x * 2
    """

    request_payload = {
        "project_context": {
            "files_changed": [{"path": "src/utils.py", "change_type": "modified"}],
            "related_tests": [],
        },
        "git_diff": git_diff,
    }

    mock_response = ImpactAnalysisResponse(
        impacted_tests=[
            ImpactItem(
                test_path="tests/test_utils.py",
                impact_score=0.1,
                severity="informational",
                reasons=["Non-functional change in helper: Comment-only changes"],
            )
        ],
        severity="informational",
        suggested_action="no-action",
    )

    with patch(
        "app.api.v1.routes.get_impact_analyzer_context",
        create_mock_impact_analyzer_context(mock_response),
    ):
        response = client.post("/analysis/impact", json=request_payload)

    assert response.status_code == 200
    response_data = response.json()

    # Verify informational severity is returned
    assert response_data["severity"] == "informational"
    assert response_data["suggested_action"] == "no-action"

    # Verify impacted test has informational severity
    assert len(response_data["impacted_tests"]) == 1
    assert response_data["impacted_tests"][0]["severity"] == "informational"
    assert response_data["impacted_tests"][0]["impact_score"] == 0.1
    assert "non-functional" in response_data["impacted_tests"][0]["reasons"][0].lower()


def test_analyze_impact_mixed_functional_and_informational():
    """Test that mixed changes prioritize functional severity."""
    client = TestClient(app)

    request_payload = {
        "project_context": {
            "files_changed": [
                {"path": "src/utils.py", "change_type": "modified"},
                {"path": "src/helper.py", "change_type": "modified"},
            ],
            "related_tests": [],
        },
        "git_diff": "...",  # Mixed changes
    }

    # Mock response with both functional and informational impacts
    mock_response = ImpactAnalysisResponse(
        impacted_tests=[
            ImpactItem(
                test_path="tests/test_utils.py",
                impact_score=0.9,
                severity="high",
                reasons=["Test calls modified function 'process' (via graph analysis)"],
            ),
            ImpactItem(
                test_path="tests/test_helper.py",
                impact_score=0.1,
                severity="informational",
                reasons=["Non-functional change in format_output: Docstring updates"],
            ),
        ],
        severity="high",  # Overall severity should be high (functional takes precedence)
        suggested_action="run-affected-tests",
    )

    with patch(
        "app.api.v1.routes.get_impact_analyzer_context",
        create_mock_impact_analyzer_context(mock_response),
    ):
        response = client.post("/analysis/impact", json=request_payload)

    assert response.status_code == 200
    response_data = response.json()

    # Verify functional severity takes precedence
    assert response_data["severity"] == "high"
    assert response_data["suggested_action"] == "run-affected-tests"

    # Verify both impact types are present
    assert len(response_data["impacted_tests"]) == 2
    severities = [item["severity"] for item in response_data["impacted_tests"]]
    assert "high" in severities
    assert "informational" in severities


def test_analyze_impact_informational_only_no_action():
    """Test that informational-only changes suggest no-action."""
    client = TestClient(app)

    request_payload = {
        "project_context": {
            "files_changed": [{"path": "src/utils.py", "change_type": "modified"}],
            "related_tests": [],
        },
        "git_diff": "# Only whitespace and comment changes",
    }

    mock_response = ImpactAnalysisResponse(
        impacted_tests=[
            ImpactItem(
                test_path="tests/test_utils.py",
                impact_score=0.1,
                severity="informational",
                reasons=["Non-functional change: Whitespace/formatting changes"],
            )
        ],
        severity="informational",
        suggested_action="no-action",
    )

    with patch(
        "app.api.v1.routes.get_impact_analyzer_context",
        create_mock_impact_analyzer_context(mock_response),
    ):
        response = client.post("/analysis/impact", json=request_payload)

    assert response.status_code == 200
    response_data = response.json()

    # Verify no action is suggested for informational-only changes
    assert response_data["severity"] == "informational"
    assert response_data["suggested_action"] == "no-action"

    # Verify low impact score
    assert response_data["impacted_tests"][0]["impact_score"] == 0.1
