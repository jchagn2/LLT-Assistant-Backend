"""Tests for LLM analyzer JSON extraction and retry logic."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.analyzers.ast_parser import ParsedTestFile, TestFunctionInfo
from app.core.analysis.llm_analyzer import LLMAnalyzer
from app.core.utils.json_extractor import JSONExtractionError


@pytest.fixture
def mock_llm_client():
    """Create a mock LLM client for testing."""
    client = AsyncMock()
    client.chat_completion = AsyncMock()
    return client


@pytest.fixture
def sample_test_func():
    """Create a sample test function info for testing."""
    return TestFunctionInfo(
        name="test_example",
        line_number=10,
        decorators=[],
        parameters=[],
        assertions=[],
        has_docstring=True,
        body_lines=(10, 12),
        source_code="def test_example():\n    assert True",
        class_name=None,
    )


@pytest.fixture
def sample_parsed_file():
    """Create a sample parsed test file for testing."""
    return ParsedTestFile(
        file_path="test_example.py",
        imports=[],
        fixtures=[],
        test_functions=[],
        test_classes=[],
    )


class TestAssertionQualityJSONExtraction:
    """Test assertion quality analysis with various JSON formats."""

    @pytest.mark.asyncio
    async def test_pure_json_response(
        self, mock_llm_client, sample_test_func, sample_parsed_file
    ):
        """Test parsing pure JSON response."""
        mock_llm_client.chat_completion.return_value = """{
            "issues": [
                {
                    "type": "weak-assertion",
                    "line": 2,
                    "severity": "warning",
                    "message": "Assertion is too simple",
                    "suggestion": "Use more specific assertion",
                    "example_code": "assert result == expected"
                }
            ],
            "overall_quality": "fair",
            "confidence": 0.85
        }"""

        analyzer = LLMAnalyzer(mock_llm_client)
        issues = await analyzer.analyze_assertion_quality(
            sample_test_func, sample_parsed_file
        )

        assert len(issues) == 1
        assert issues[0].type == "llm-weak-assertion"
        assert issues[0].severity == "warning"
        mock_llm_client.chat_completion.assert_called_once()

    @pytest.mark.asyncio
    async def test_markdown_wrapped_json(
        self, mock_llm_client, sample_test_func, sample_parsed_file
    ):
        """Test parsing JSON wrapped in markdown code block."""
        mock_llm_client.chat_completion.return_value = """Here is my analysis:

```json
{
    "issues": [
        {
            "type": "missing-assertion",
            "line": 3,
            "severity": "error",
            "message": "Missing assertion for edge case",
            "suggestion": "Add assertion for None input",
            "example_code": "assert func(None) raises ValueError"
        }
    ],
    "overall_quality": "poor",
    "confidence": 0.9
}
```

This test needs improvement."""

        analyzer = LLMAnalyzer(mock_llm_client)
        issues = await analyzer.analyze_assertion_quality(
            sample_test_func, sample_parsed_file
        )

        assert len(issues) == 1
        assert issues[0].type == "llm-missing-assertion"
        assert issues[0].severity == "error"

    @pytest.mark.asyncio
    async def test_retry_on_invalid_json_then_success(
        self, mock_llm_client, sample_test_func, sample_parsed_file
    ):
        """Test retry logic when first response is invalid JSON."""
        # First call returns invalid JSON, second call returns valid
        mock_llm_client.chat_completion.side_effect = [
            "This is not JSON at all",
            """{
                "issues": [],
                "overall_quality": "good",
                "confidence": 0.8
            }""",
        ]

        analyzer = LLMAnalyzer(mock_llm_client)
        issues = await analyzer.analyze_assertion_quality(
            sample_test_func, sample_parsed_file
        )

        assert len(issues) == 0
        assert mock_llm_client.chat_completion.call_count == 2

    @pytest.mark.asyncio
    async def test_empty_response_triggers_retry(
        self, mock_llm_client, sample_test_func, sample_parsed_file
    ):
        """Test that empty response triggers retry."""
        mock_llm_client.chat_completion.side_effect = [
            "",  # Empty response
            """{
                "issues": [],
                "overall_quality": "good",
                "confidence": 0.75
            }""",
        ]

        analyzer = LLMAnalyzer(mock_llm_client)
        issues = await analyzer.analyze_assertion_quality(
            sample_test_func, sample_parsed_file
        )

        assert len(issues) == 0
        assert mock_llm_client.chat_completion.call_count == 2

    @pytest.mark.asyncio
    async def test_max_retries_exhausted_returns_empty(
        self, mock_llm_client, sample_test_func, sample_parsed_file
    ):
        """Test that exhausting retries returns empty list."""
        mock_llm_client.chat_completion.side_effect = [
            "Invalid JSON response 1",
            "Invalid JSON response 2",
        ]

        analyzer = LLMAnalyzer(mock_llm_client)
        issues = await analyzer.analyze_assertion_quality(
            sample_test_func, sample_parsed_file
        )

        assert len(issues) == 0
        assert mock_llm_client.chat_completion.call_count == 2

    @pytest.mark.asyncio
    async def test_missing_required_fields_triggers_retry(
        self, mock_llm_client, sample_test_func, sample_parsed_file
    ):
        """Test that missing required fields triggers retry."""
        mock_llm_client.chat_completion.side_effect = [
            '{"confidence": 0.8}',  # Missing "issues" field
            """{
                "issues": [],
                "overall_quality": "good",
                "confidence": 0.8
            }""",
        ]

        analyzer = LLMAnalyzer(mock_llm_client)
        issues = await analyzer.analyze_assertion_quality(
            sample_test_func, sample_parsed_file
        )

        assert len(issues) == 0
        assert mock_llm_client.chat_completion.call_count == 2

    @pytest.mark.asyncio
    async def test_filters_low_confidence_issues(
        self, mock_llm_client, sample_test_func, sample_parsed_file
    ):
        """Test that low confidence issues are filtered out."""
        mock_llm_client.chat_completion.return_value = """{
            "issues": [
                {
                    "type": "weak-assertion",
                    "line": 2,
                    "severity": "warning",
                    "message": "Low confidence issue",
                    "suggestion": "Ignore this",
                    "example_code": "assert True",
                    "confidence": 0.5
                },
                {
                    "type": "missing-assertion",
                    "line": 3,
                    "severity": "error",
                    "message": "High confidence issue",
                    "suggestion": "Fix this",
                    "example_code": "assert result is not None",
                    "confidence": 0.9
                }
            ],
            "overall_quality": "fair",
            "confidence": 0.75
        }"""

        analyzer = LLMAnalyzer(mock_llm_client)
        issues = await analyzer.analyze_assertion_quality(
            sample_test_func, sample_parsed_file
        )

        # Only high confidence issue should be returned
        assert len(issues) == 1
        assert issues[0].type == "llm-missing-assertion"


class TestTestSmellJSONExtraction:
    """Test test smell analysis with various JSON formats."""

    @pytest.mark.asyncio
    async def test_smell_detection_with_markdown(
        self, mock_llm_client, sample_test_func, sample_parsed_file
    ):
        """Test smell detection with markdown-wrapped JSON."""
        mock_llm_client.chat_completion.return_value = """Based on my analysis:

```json
{
    "smells": [
        {
            "type": "flaky-timing",
            "line": 5,
            "severity": "error",
            "description": "Uses time.sleep() which causes flaky tests",
            "impact": "Test may fail randomly due to timing issues",
            "suggestion": "Use pytest fixtures or mocking instead",
            "example_code": "mock_time.sleep = Mock()"
        }
    ],
    "confidence": 0.95
}
```"""

        analyzer = LLMAnalyzer(mock_llm_client)
        issues = await analyzer.analyze_test_smells(
            sample_test_func, sample_parsed_file
        )

        assert len(issues) == 1
        assert "test-smell-flaky-timing" in issues[0].type
        assert issues[0].severity == "error"

    @pytest.mark.asyncio
    async def test_smell_retry_logic(
        self, mock_llm_client, sample_test_func, sample_parsed_file
    ):
        """Test retry logic for smell detection."""
        mock_llm_client.chat_completion.side_effect = [
            "Not valid JSON",
            """{
                "smells": [],
                "confidence": 0.8
            }""",
        ]

        analyzer = LLMAnalyzer(mock_llm_client)
        issues = await analyzer.analyze_test_smells(
            sample_test_func, sample_parsed_file
        )

        assert len(issues) == 0
        assert mock_llm_client.chat_completion.call_count == 2


class TestMergeabilityJSONExtraction:
    """Test mergeability analysis with various JSON formats."""

    @pytest.mark.asyncio
    async def test_mergeable_tests_detection(
        self, mock_llm_client, sample_test_func, sample_parsed_file
    ):
        """Test detection of mergeable tests."""
        test2 = TestFunctionInfo(
            name="test_example_2",
            line_number=20,
            decorators=[],
            parameters=[],
            assertions=[],
            has_docstring=True,
            body_lines=(20, 22),
            source_code="def test_example_2():\n    assert False",
            class_name=None,
        )

        mock_llm_client.chat_completion.return_value = """{
            "mergeable": true,
            "confidence": 0.9,
            "reason": "Both tests verify the same functionality",
            "merged_test_name": "test_combined_example",
            "concerns": []
        }"""

        analyzer = LLMAnalyzer(mock_llm_client)
        issue = await analyzer.analyze_mergeability(
            sample_test_func, test2, sample_parsed_file
        )

        assert issue is not None
        assert issue.type == "mergeable-tests"
        assert issue.severity == "info"

    @pytest.mark.asyncio
    async def test_non_mergeable_tests(
        self, mock_llm_client, sample_test_func, sample_parsed_file
    ):
        """Test detection of non-mergeable tests."""
        test2 = TestFunctionInfo(
            name="test_different",
            line_number=20,
            decorators=[],
            parameters=[],
            assertions=[],
            has_docstring=True,
            body_lines=(20, 22),
            source_code="def test_different():\n    assert True",
            class_name=None,
        )

        mock_llm_client.chat_completion.return_value = """{
            "mergeable": false,
            "confidence": 0.85,
            "reason": "Tests verify different aspects",
            "merged_test_name": null,
            "concerns": ["Would violate single responsibility principle"]
        }"""

        analyzer = LLMAnalyzer(mock_llm_client)
        issue = await analyzer.analyze_mergeability(
            sample_test_func, test2, sample_parsed_file
        )

        assert issue is None

    @pytest.mark.asyncio
    async def test_mergeability_retry_with_markdown(
        self, mock_llm_client, sample_test_func, sample_parsed_file
    ):
        """Test retry logic for mergeability with markdown response."""
        test2 = TestFunctionInfo(
            name="test_example_2",
            line_number=20,
            decorators=[],
            parameters=[],
            assertions=[],
            has_docstring=False,
            body_lines=(20, 21),
            source_code="def test_example_2():\n    pass",
            class_name=None,
        )

        mock_llm_client.chat_completion.side_effect = [
            """Here's my analysis:
            ```json
            {
                "mergeable": true,
                "confidence": 0.8,
                "reason": "Tests are similar",
                "merged_test_name": "test_merged",
                "concerns": []
            }
            ```""",
        ]

        analyzer = LLMAnalyzer(mock_llm_client)
        issue = await analyzer.analyze_mergeability(
            sample_test_func, test2, sample_parsed_file
        )

        assert issue is not None
        mock_llm_client.chat_completion.assert_called_once()
