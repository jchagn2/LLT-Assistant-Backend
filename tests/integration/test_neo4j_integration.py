"""
Integration tests for Neo4j graph database.

These tests require a running Neo4j instance and test end-to-end workflows.
"""

import pytest

from app.api.v1.schemas import (
    CallRelationship,
    ImportRelationship,
    SymbolNode,
)
from app.core.graph.graph_service import GraphService


@pytest.mark.integration
@pytest.mark.asyncio
async def test_neo4j_connection():
    """Test basic Neo4j connectivity."""
    service = GraphService()

    try:
        await service.connect()
        result = await service.client.execute_query("RETURN 1 as value")
        assert result[0]["value"] == 1
    finally:
        await service.close()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_symbol_ingestion_workflow():
    """Test complete symbol ingestion and query workflow."""
    service = GraphService()

    try:
        await service.connect()
        await service.create_indexes()

        # Create test symbols
        symbols = [
            {
                "name": "function_a",
                "qualified_name": "test.function_a",
                "kind": "function",
                "signature": "function_a() -> None",
                "file_path": "/test/test.py",
                "line_start": 10,
                "line_end": 15,
            },
            {
                "name": "function_b",
                "qualified_name": "test.function_b",
                "kind": "function",
                "signature": "function_b() -> None",
                "file_path": "/test/test.py",
                "line_start": 20,
                "line_end": 25,
            },
        ]

        calls = [
            {
                "caller_qualified_name": "test.function_a",
                "callee_qualified_name": "test.function_b",
                "line": 12,
            }
        ]

        # Ingest symbols
        stats = await service.ingest_symbols(
            symbols=symbols,
            calls=calls,
            imports=[],
            project_id="test-integration",
        )

        assert stats["nodes_created"] >= 2
        assert stats["relationships_created"] >= 1
        assert stats["processing_time_ms"] < 2000

        # Query function
        result = await service.query_function_dependencies(
            function_name="function_a",
            project_id="test-integration",
        )

        assert result["function"] is not None
        assert result["function"]["name"] == "function_a"
        assert len(result["dependencies"]) >= 1
        assert result["query_time_ms"] < 100

    finally:
        # Cleanup test data
        await service.client.execute_query(
            "MATCH (s:Symbol {project_id: 'test-integration'}) DETACH DELETE s"
        )
        await service.close()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_performance_batch_insert():
    """Test batch insert performance (100 nodes, 200 relationships)."""
    service = GraphService()

    try:
        await service.connect()

        # Generate 100 test symbols
        symbols = [
            {
                "name": f"function_{i}",
                "qualified_name": f"perf_test.function_{i}",
                "kind": "function",
                "signature": f"function_{i}() -> None",
                "file_path": "/test/perf.py",
                "line_start": i * 10,
                "line_end": i * 10 + 5,
            }
            for i in range(100)
        ]

        # Generate 200 call relationships
        calls = []
        for i in range(99):
            calls.append(
                {
                    "caller_qualified_name": f"perf_test.function_{i}",
                    "callee_qualified_name": f"perf_test.function_{i + 1}",
                    "line": i * 10 + 2,
                }
            )
        for i in range(99):
            calls.append(
                {
                    "caller_qualified_name": f"perf_test.function_{i}",
                    "callee_qualified_name": f"perf_test.function_{(i + 2) % 100}",
                    "line": i * 10 + 3,
                }
            )

        # Ingest and measure performance
        stats = await service.ingest_symbols(
            symbols=symbols,
            calls=calls,
            imports=[],
            project_id="perf-test",
        )

        # Performance assertions
        assert stats["nodes_created"] == 100
        assert stats["relationships_created"] >= 198
        assert (
            stats["processing_time_ms"] < 2000
        ), f"Batch insert took {stats['processing_time_ms']}ms (expected < 2000ms)"

    finally:
        # Cleanup
        await service.client.execute_query(
            "MATCH (s:Symbol {project_id: 'perf-test'}) DETACH DELETE s"
        )
        await service.close()
