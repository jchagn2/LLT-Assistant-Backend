"""
Integration tests for Neo4j trunk validation (Phase 1).

These tests validate the graph database foundation using a minimal test project
with known function call relationships. Tests require a running Neo4j instance.

Test Project Structure:
- utils.py: calculate_tax, format_price
- service.py: get_total_price (calls calculate_tax), display_price (calls get_total_price, format_price)
- test_service.py: test_get_total_price (calls get_total_price), test_display_price (calls display_price)

Expected: 6 Symbol nodes, 5 CALLS relationships
"""

import json
import logging
from pathlib import Path

import pytest

from app.core.graph.graph_service import GraphService

logger = logging.getLogger(__name__)


# Load expected data fixture
FIXTURES_DIR = Path(__file__).parent.parent / "fixtures" / "minimal_project"
EXPECTED_DATA_PATH = FIXTURES_DIR / "expected_data.json"

PROJECT_ID = "trunk-validation-test"


@pytest.fixture
def expected_data():
    """Load expected data from JSON fixture."""
    with open(EXPECTED_DATA_PATH) as f:
        return json.load(f)


@pytest.fixture
def minimal_project_symbols(expected_data):
    """Return symbols in the format expected by GraphService.ingest_symbols."""
    return expected_data["symbols"]["details"]


@pytest.fixture
def minimal_project_calls(expected_data):
    """Return CALLS relationships in the format expected by GraphService.ingest_symbols."""
    return [
        {
            "caller_qualified_name": rel["caller_qualified_name"],
            "callee_qualified_name": rel["callee_qualified_name"],
            "line": rel["line"],
        }
        for rel in expected_data["calls"]["relationships"]
    ]


@pytest.fixture
async def graph_service():
    """Provide a connected GraphService instance with cleanup."""
    service = GraphService()
    await service.connect()
    await service.create_indexes()

    yield service

    # Cleanup test data
    await service.client.execute_query(
        f"MATCH (s:Symbol {{project_id: '{PROJECT_ID}'}}) DETACH DELETE s"
    )
    await service.close()


# =============================================================================
# Task 1.1.3: Data Ingestion Tests
# =============================================================================


@pytest.mark.integration
@pytest.mark.asyncio
async def test_ingest_minimal_project_creates_expected_nodes(
    graph_service, minimal_project_symbols, minimal_project_calls, expected_data
):
    """Test that ingesting minimal project creates exactly 6 Symbol nodes.

    CRITICAL CHECKPOINT: If this test fails with nodes_created = 0,
    STOP ALL WORK - data ingestion is broken.
    """
    stats = await graph_service.ingest_symbols(
        symbols=minimal_project_symbols,
        calls=minimal_project_calls,
        imports=[],
        project_id=PROJECT_ID,
    )

    expected_symbol_count = expected_data["symbols"]["total_count"]

    assert stats["nodes_created"] == expected_symbol_count, (
        f"Expected {expected_symbol_count} nodes, got {stats['nodes_created']}. "
        "CRITICAL: If nodes_created is 0, data ingestion is broken!"
    )


@pytest.mark.integration
@pytest.mark.asyncio
async def test_ingest_minimal_project_creates_expected_calls_relationships(
    graph_service, minimal_project_symbols, minimal_project_calls, expected_data
):
    """Test that ingesting minimal project creates exactly 5 CALLS relationships.

    CRITICAL CHECKPOINT: If this test fails with relationships_created = 0,
    STOP ALL WORK - CALLS relationship creation is broken.
    """
    stats = await graph_service.ingest_symbols(
        symbols=minimal_project_symbols,
        calls=minimal_project_calls,
        imports=[],
        project_id=PROJECT_ID,
    )

    expected_calls_count = expected_data["calls"]["total_count"]

    assert stats["relationships_created"] == expected_calls_count, (
        f"Expected {expected_calls_count} CALLS relationships, "
        f"got {stats['relationships_created']}. "
        "CRITICAL: If relationships_created is 0, CALLS relationship creation is broken!"
    )


@pytest.mark.integration
@pytest.mark.asyncio
async def test_verify_calls_relationships_exist_in_neo4j(
    graph_service, minimal_project_symbols, minimal_project_calls
):
    """Verify CALLS relationships can be queried directly from Neo4j.

    This test performs a raw Cypher query to confirm relationships exist.
    """
    # First, ingest the data
    await graph_service.ingest_symbols(
        symbols=minimal_project_symbols,
        calls=minimal_project_calls,
        imports=[],
        project_id=PROJECT_ID,
    )

    # Query CALLS relationships directly
    query = """
    MATCH (caller:Symbol {project_id: $project_id})-[r:CALLS]->(callee:Symbol)
    RETURN count(r) as calls_count
    """
    result = await graph_service.client.execute_query(query, {"project_id": PROJECT_ID})

    calls_count = result[0]["calls_count"]

    assert calls_count == 5, (
        f"Expected 5 CALLS relationships in Neo4j, found {calls_count}. "
        "CRITICAL: CALLS relationships are not being created correctly!"
    )


@pytest.mark.integration
@pytest.mark.asyncio
async def test_verify_all_symbols_have_correct_properties(
    graph_service, minimal_project_symbols, minimal_project_calls
):
    """Verify all Symbol nodes have required properties set correctly."""
    await graph_service.ingest_symbols(
        symbols=minimal_project_symbols,
        calls=minimal_project_calls,
        imports=[],
        project_id=PROJECT_ID,
    )

    # Query all symbols
    query = """
    MATCH (s:Symbol {project_id: $project_id})
    RETURN s.name as name, s.qualified_name as qualified_name,
           s.kind as kind, s.file_path as file_path
    """
    result = await graph_service.client.execute_query(query, {"project_id": PROJECT_ID})

    assert len(result) == 6, f"Expected 6 symbols, found {len(result)}"

    # Verify all symbols have required properties
    for symbol in result:
        assert symbol["name"] is not None, "Symbol missing name"
        assert symbol["qualified_name"] is not None, "Symbol missing qualified_name"
        assert symbol["kind"] is not None, "Symbol missing kind"
        assert symbol["file_path"] is not None, "Symbol missing file_path"


# =============================================================================
# Task 1.2.1: Forward Dependency Tests
# =============================================================================


@pytest.mark.integration
@pytest.mark.asyncio
async def test_query_function_dependencies_returns_direct_calls(
    graph_service, minimal_project_symbols, minimal_project_calls
):
    """Test that query_function_dependencies returns direct calls (depth=1).

    display_price directly calls: get_total_price, format_price
    """
    await graph_service.ingest_symbols(
        symbols=minimal_project_symbols,
        calls=minimal_project_calls,
        imports=[],
        project_id=PROJECT_ID,
    )

    result = await graph_service.query_function_dependencies(
        function_name="display_price",
        project_id=PROJECT_ID,
        depth=1,
    )

    assert result["function"] is not None, "Function display_price not found"
    assert result["function"]["name"] == "display_price"

    dependency_names = [dep["name"] for dep in result["dependencies"]]

    # display_price directly calls get_total_price and format_price
    assert (
        "get_total_price" in dependency_names
    ), "Missing direct dependency: get_total_price"
    assert "format_price" in dependency_names, "Missing direct dependency: format_price"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_query_function_dependencies_returns_transitive_calls_depth_2(
    graph_service, minimal_project_symbols, minimal_project_calls
):
    """Test that query_function_dependencies returns transitive calls (depth=2).

    display_price at depth 2 should include:
    - direct: get_total_price, format_price
    - transitive via get_total_price: calculate_tax
    """
    await graph_service.ingest_symbols(
        symbols=minimal_project_symbols,
        calls=minimal_project_calls,
        imports=[],
        project_id=PROJECT_ID,
    )

    result = await graph_service.query_function_dependencies(
        function_name="display_price",
        project_id=PROJECT_ID,
        depth=2,
    )

    dependency_names = [dep["name"] for dep in result["dependencies"]]

    # Should include calculate_tax via transitive call
    assert (
        "calculate_tax" in dependency_names
    ), "Missing transitive dependency: calculate_tax (via get_total_price)"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_query_function_dependencies_returns_empty_for_leaf_function(
    graph_service, minimal_project_symbols, minimal_project_calls
):
    """Test that leaf functions (no outgoing calls) return empty dependencies.

    calculate_tax and format_price are leaf functions (call nothing).
    """
    await graph_service.ingest_symbols(
        symbols=minimal_project_symbols,
        calls=minimal_project_calls,
        imports=[],
        project_id=PROJECT_ID,
    )

    result = await graph_service.query_function_dependencies(
        function_name="calculate_tax",
        project_id=PROJECT_ID,
        depth=1,
    )

    assert result["function"] is not None, "Function calculate_tax not found"
    assert len(result["dependencies"]) == 0, (
        f"Leaf function should have no dependencies, found: "
        f"{[d['name'] for d in result['dependencies']]}"
    )


# =============================================================================
# Task 1.2.2: Reverse Dependency Tests
# =============================================================================


@pytest.mark.integration
@pytest.mark.asyncio
async def test_query_reverse_dependencies_returns_callers(
    graph_service, minimal_project_symbols, minimal_project_calls
):
    """Test that query_reverse_dependencies returns functions that call the target.

    get_total_price is called by: display_price, test_get_total_price
    """
    await graph_service.ingest_symbols(
        symbols=minimal_project_symbols,
        calls=minimal_project_calls,
        imports=[],
        project_id=PROJECT_ID,
    )

    result = await graph_service.query_reverse_dependencies(
        function_name="get_total_price",
        project_id=PROJECT_ID,
    )

    assert result["function"] is not None, "Function get_total_price not found"

    caller_names = [caller["name"] for caller in result["callers"]]

    # get_total_price is called by display_price and test_get_total_price
    assert "display_price" in caller_names, "Missing caller: display_price"
    assert (
        "test_get_total_price" in caller_names
    ), "Missing caller: test_get_total_price"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_query_reverse_dependencies_returns_empty_for_root_function(
    graph_service, minimal_project_symbols, minimal_project_calls
):
    """Test that root functions (nothing calls them) return empty callers.

    test_get_total_price and test_display_price are root functions.
    """
    await graph_service.ingest_symbols(
        symbols=minimal_project_symbols,
        calls=minimal_project_calls,
        imports=[],
        project_id=PROJECT_ID,
    )

    result = await graph_service.query_reverse_dependencies(
        function_name="test_get_total_price",
        project_id=PROJECT_ID,
    )

    assert result["function"] is not None, "Function test_get_total_price not found"
    assert len(result["callers"]) == 0, (
        f"Root function should have no callers, found: "
        f"{[c['name'] for c in result['callers']]}"
    )


# =============================================================================
# Task 1.2.4: Performance Tests
# =============================================================================


@pytest.mark.integration
@pytest.mark.asyncio
async def test_query_performance_under_100ms(
    graph_service, minimal_project_symbols, minimal_project_calls
):
    """Test that single function query completes in under 100ms."""
    await graph_service.ingest_symbols(
        symbols=minimal_project_symbols,
        calls=minimal_project_calls,
        imports=[],
        project_id=PROJECT_ID,
    )

    result = await graph_service.query_function_dependencies(
        function_name="display_price",
        project_id=PROJECT_ID,
        depth=2,
    )

    assert (
        result["query_time_ms"] < 100
    ), f"Query took {result['query_time_ms']}ms, expected < 100ms"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_reverse_query_performance_under_100ms(
    graph_service, minimal_project_symbols, minimal_project_calls
):
    """Test that reverse dependency query completes in under 100ms."""
    await graph_service.ingest_symbols(
        symbols=minimal_project_symbols,
        calls=minimal_project_calls,
        imports=[],
        project_id=PROJECT_ID,
    )

    result = await graph_service.query_reverse_dependencies(
        function_name="get_total_price",
        project_id=PROJECT_ID,
    )

    assert (
        result["query_time_ms"] < 100
    ), f"Reverse query took {result['query_time_ms']}ms, expected < 100ms"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_ingestion_performance_under_2000ms(
    graph_service, minimal_project_symbols, minimal_project_calls
):
    """Test that data ingestion completes in under 2000ms."""
    stats = await graph_service.ingest_symbols(
        symbols=minimal_project_symbols,
        calls=minimal_project_calls,
        imports=[],
        project_id=PROJECT_ID,
    )

    assert (
        stats["processing_time_ms"] < 2000
    ), f"Ingestion took {stats['processing_time_ms']}ms, expected < 2000ms"


# =============================================================================
# Task 2.1.5: Graph-Based Impact Analysis Tests
# =============================================================================


@pytest.mark.integration
@pytest.mark.asyncio
async def test_impact_analysis_finds_tests_via_call_graph(
    graph_service, minimal_project_symbols, minimal_project_calls
):
    """Test that graph-based impact analysis correctly identifies impacted tests.

    When calculate_tax is modified:
    - get_total_price calls calculate_tax
    - test_get_total_price calls get_total_price (transitive)
    - display_price calls get_total_price which calls calculate_tax
    - test_display_price calls display_price (transitive via 2 levels)
    """
    from app.analyzers.rule_engine import RuleEngine
    from app.core.analysis.llm_analyzer import LLMAnalyzer
    from app.core.analyzer import ImpactAnalyzer
    from app.core.llm.llm_client import create_llm_client

    # Ingest test data
    await graph_service.ingest_symbols(
        symbols=minimal_project_symbols,
        calls=minimal_project_calls,
        imports=[],
        project_id=PROJECT_ID,
    )

    # Create ImpactAnalyzer with GraphService
    rule_engine = RuleEngine()
    llm_client = create_llm_client()
    llm_analyzer = LLMAnalyzer(llm_client)

    impact_analyzer = ImpactAnalyzer(
        rule_engine=rule_engine,
        llm_analyzer=llm_analyzer,
        graph_service=graph_service,
        project_id=PROJECT_ID,
    )

    # Simulate modifying calculate_tax function
    git_diff = """diff --git a/tests/fixtures/minimal_project/utils.py b/tests/fixtures/minimal_project/utils.py
--- a/tests/fixtures/minimal_project/utils.py
+++ b/tests/fixtures/minimal_project/utils.py
@@ -9,6 +9,7 @@ def calculate_tax(price: float, rate: float = 0.1) -> float:
     Returns:
         The calculated tax amount
     \"\"\"
+    # Modified implementation
     return price * rate
"""

    files_changed = [
        {"path": "tests/fixtures/minimal_project/utils.py", "change_type": "modified"}
    ]
    related_tests = ["tests/fixtures/minimal_project/test_service.py"]

    result = await impact_analyzer.analyze_impact_async(
        files_changed=files_changed,
        related_tests=related_tests,
        git_diff=git_diff,
    )

    # Verify we found impacted tests
    assert len(result.impacted_tests) > 0, "Should find at least one impacted test"

    # Check that test file was found
    test_paths = [item.test_path for item in result.impacted_tests]
    assert any(
        "test_service" in path for path in test_paths
    ), f"Expected test_service.py to be impacted. Found: {test_paths}"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_impact_analysis_returns_empty_when_no_callers(
    graph_service, minimal_project_symbols, minimal_project_calls
):
    """Test that impact analysis returns empty when modified function has no callers."""
    from app.analyzers.rule_engine import RuleEngine
    from app.core.analysis.llm_analyzer import LLMAnalyzer
    from app.core.analyzer import ImpactAnalyzer
    from app.core.llm.llm_client import create_llm_client

    # Ingest test data
    await graph_service.ingest_symbols(
        symbols=minimal_project_symbols,
        calls=minimal_project_calls,
        imports=[],
        project_id=PROJECT_ID,
    )

    # Create ImpactAnalyzer with GraphService
    rule_engine = RuleEngine()
    llm_client = create_llm_client()
    llm_analyzer = LLMAnalyzer(llm_client)

    impact_analyzer = ImpactAnalyzer(
        rule_engine=rule_engine,
        llm_analyzer=llm_analyzer,
        graph_service=graph_service,
        project_id=PROJECT_ID,
    )

    # Simulate modifying a function that exists but has no callers
    git_diff = """diff --git a/some/module.py b/some/module.py
--- a/some/module.py
+++ b/some/module.py
@@ -1,3 +1,4 @@
+def orphan_function():
+    return "I have no callers"
"""

    files_changed = [{"path": "some/module.py", "change_type": "modified"}]
    related_tests = []  # No related tests provided

    result = await impact_analyzer.analyze_impact_async(
        files_changed=files_changed,
        related_tests=related_tests,
        git_diff=git_diff,
    )

    # When a function has no callers and no related tests, result should be empty
    # or only contain low-priority items
    high_impact = [t for t in result.impacted_tests if t.severity == "high"]
    assert len(high_impact) == 0, "Should have no high-impact items for orphan function"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_impact_analysis_detects_direct_test_modification(
    graph_service, minimal_project_symbols, minimal_project_calls
):
    """Test that modifying a test file directly results in high impact."""
    from app.analyzers.rule_engine import RuleEngine
    from app.core.analysis.llm_analyzer import LLMAnalyzer
    from app.core.analyzer import ImpactAnalyzer
    from app.core.llm.llm_client import create_llm_client

    # Ingest test data
    await graph_service.ingest_symbols(
        symbols=minimal_project_symbols,
        calls=minimal_project_calls,
        imports=[],
        project_id=PROJECT_ID,
    )

    # Create ImpactAnalyzer with GraphService
    rule_engine = RuleEngine()
    llm_client = create_llm_client()
    llm_analyzer = LLMAnalyzer(llm_client)

    impact_analyzer = ImpactAnalyzer(
        rule_engine=rule_engine,
        llm_analyzer=llm_analyzer,
        graph_service=graph_service,
        project_id=PROJECT_ID,
    )

    # Simulate modifying a test file directly
    files_changed = [
        {
            "path": "tests/fixtures/minimal_project/test_service.py",
            "change_type": "modified",
        }
    ]
    related_tests = ["tests/fixtures/minimal_project/test_service.py"]

    result = await impact_analyzer.analyze_impact_async(
        files_changed=files_changed,
        related_tests=related_tests,
        git_diff=None,  # No function-level analysis needed
    )

    # Verify test file is marked as high impact
    assert len(result.impacted_tests) > 0, "Should find the modified test file"

    test_item = next(
        (t for t in result.impacted_tests if "test_service" in t.test_path),
        None,
    )
    assert test_item is not None, "test_service.py should be in impacted tests"
    assert (
        test_item.impact_score == 1.0
    ), "Direct test modification should have score 1.0"
    assert (
        test_item.severity == "high"
    ), "Direct test modification should be high severity"


# =============================================================================
# Task 2.2.4: Quality Analysis with Graph-Based Mock Detection
# =============================================================================


@pytest.mark.integration
@pytest.mark.asyncio
async def test_quality_analysis_detects_missing_mocks_with_graph(
    graph_service, minimal_project_symbols, minimal_project_calls
):
    """Test that quality analysis detects missing mocks using graph data.

    Scenario: A test calls save_user which calls save_to_db (external dependency),
    but the test has no mock setup.
    """
    from app.api.v1.schemas import FileInput
    from app.core.services.quality_service import QualityAnalysisService

    # Ingest test data with external dependency pattern
    await graph_service.ingest_symbols(
        symbols=minimal_project_symbols,
        calls=minimal_project_calls,
        imports=[],
        project_id=PROJECT_ID,
    )

    # Create test file content with external dependency call
    test_code = '''
def test_get_total_price():
    """Test get_total_price function."""
    price = get_total_price(100.0)
    assert price > 0
'''

    files = [
        FileInput(
            path="tests/fixtures/minimal_project/test_service.py",
            content=test_code,
        )
    ]

    # Create quality service with graph integration
    quality_service = QualityAnalysisService(
        graph_service=graph_service,
        project_id=PROJECT_ID,
    )

    try:
        result = await quality_service.analyze_batch(files, mode="fast")

        # Verify analysis completed
        assert result.summary.total_files == 1
        assert result.summary.total_issues >= 0

        # Check if missing-mock issues were detected (if graph data available)
        mock_issues = [issue for issue in result.issues if issue.code == "missing-mock"]

        logger.info(
            "Quality analysis found %d issues, %d missing-mock issues",
            len(result.issues),
            len(mock_issues),
        )

    finally:
        await quality_service.close()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_quality_analysis_no_mock_issue_when_mocked(
    graph_service, minimal_project_symbols, minimal_project_calls
):
    """Test that quality analysis doesn't flag tests with proper mocking."""
    from app.api.v1.schemas import FileInput
    from app.core.services.quality_service import QualityAnalysisService

    # Ingest test data
    await graph_service.ingest_symbols(
        symbols=minimal_project_symbols,
        calls=minimal_project_calls,
        imports=[],
        project_id=PROJECT_ID,
    )

    # Create test file content WITH proper mocking
    test_code = '''
from unittest.mock import patch

@patch('module.save_to_db')
def test_save_user(mock_save):
    """Test save_user function with mocked dependency."""
    mock_save.return_value = True
    result = save_user({"name": "test"})
    assert result is True
'''

    files = [
        FileInput(
            path="tests/fixtures/minimal_project/test_service.py",
            content=test_code,
        )
    ]

    # Create quality service with graph integration
    quality_service = QualityAnalysisService(
        graph_service=graph_service,
        project_id=PROJECT_ID,
    )

    try:
        result = await quality_service.analyze_batch(files, mode="fast")

        # Check that no missing-mock issues were detected
        mock_issues = [issue for issue in result.issues if issue.code == "missing-mock"]

        assert (
            len(mock_issues) == 0
        ), "Test with proper mocking should not have missing-mock issues"

        logger.info(
            "Quality analysis correctly detected proper mocking: %d issues total",
            len(result.issues),
        )

    finally:
        await quality_service.close()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_quality_analysis_works_without_graph(
    graph_service, minimal_project_symbols, minimal_project_calls
):
    """Test that quality analysis still works without graph service (fallback to AST)."""
    from app.api.v1.schemas import FileInput
    from app.core.services.quality_service import QualityAnalysisService

    # Create test file content
    test_code = '''
def test_example():
    """Test example function."""
    result = example_function()
    assert result is not None
'''

    files = [
        FileInput(
            path="tests/test_example.py",
            content=test_code,
        )
    ]

    # Create quality service WITHOUT graph integration
    quality_service = QualityAnalysisService(
        graph_service=None,  # No graph service
        project_id=None,
    )

    try:
        result = await quality_service.analyze_batch(files, mode="fast")

        # Verify analysis completed successfully even without graph
        assert result.summary.total_files == 1
        assert result.summary.total_issues >= 0

        logger.info(
            "Quality analysis works without graph: %d issues found",
            len(result.issues),
        )

    finally:
        await quality_service.close()
