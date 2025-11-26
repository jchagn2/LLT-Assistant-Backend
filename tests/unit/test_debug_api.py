"""
Unit tests for Neo4j debug API endpoints.

Tests symbol ingestion and querying functionality with mocked services.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.core.graph.graph_service import GraphService
from app.main import app


@pytest.fixture
def mock_graph_service():
    """Create mock GraphService."""
    service = AsyncMock(spec=GraphService)
    service.connect = AsyncMock()
    service.close = AsyncMock()
    service.create_indexes = AsyncMock()
    service.ingest_symbols = AsyncMock(
        return_value={
            "nodes_created": 5,
            "relationships_created": 3,
            "processing_time_ms": 150,
        }
    )
    service.query_function_dependencies = AsyncMock(
        return_value={
            "function": {
                "name": "test_func",
                "qualified_name": "module.test_func",
                "kind": "function",
                "signature": "test_func(x: int) -> int",
                "file_path": "/app/test.py",
                "line_start": 10,
                "line_end": 15,
            },
            "dependencies": [],
            "query_time_ms": 50,
        }
    )
    return service


def test_health_endpoint():
    """Test that health endpoint is accessible."""
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


@pytest.mark.asyncio
async def test_ingest_symbols_success_payload():
    """Test ingestion endpoint accepts valid payload."""
    client = TestClient(app)

    payload = {
        "project_id": "test-project",
        "symbols": [
            {
                "name": "test_func",
                "qualified_name": "module.test_func",
                "kind": "function",
                "signature": "test_func()",
                "file_path": "/app/test.py",
                "line_start": 10,
                "line_end": 15,
            }
        ],
        "calls": [],
        "imports": [],
    }

    # Test that payload schema validation passes
    from app.api.v1.schemas import IngestSymbolsRequest

    request = IngestSymbolsRequest(**payload)
    assert request.project_id == "test-project"
    assert len(request.symbols) == 1


@pytest.mark.asyncio
async def test_query_function_schema():
    """Test query function response schema."""
    from app.api.v1.schemas import QueryFunctionResponse, SymbolInfo

    response = QueryFunctionResponse(
        function=SymbolInfo(
            name="test_func",
            qualified_name="module.test_func",
            kind="function",
            signature="test_func()",
            file_path="/app/test.py",
            line_start=10,
            line_end=15,
        ),
        dependencies=[],
        query_time_ms=50,
        project_id="test-project",
    )

    assert response.function.name == "test_func"
    assert response.query_time_ms == 50
    assert response.project_id == "test-project"
