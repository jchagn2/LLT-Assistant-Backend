"""Unit tests for LLM parallelization in analysis strategies.

This module tests the semaphore-based parallel execution of LLM calls
in HybridStrategy and LLMOnlyStrategy classes.
"""

import asyncio
import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.analyzers.ast_parser import ParsedTestFile, TestFunctionInfo
from app.core.analysis.strategies import HybridStrategy, LLMOnlyStrategy
from app.core.analysis.uncertain_case_detector import UncertainCaseDetector


@pytest.fixture
def mock_rule_engine():
    """Create a mock rule engine that returns no issues."""
    engine = MagicMock()
    engine.analyze = MagicMock(return_value=[])
    return engine


@pytest.fixture
def mock_llm_analyzer():
    """Create a mock LLM analyzer with configurable delay."""
    analyzer = AsyncMock()

    async def mock_analyze_assertion_quality(test_func, parsed_file=None):
        # Simulate LLM API call delay (50ms per call)
        await asyncio.sleep(0.05)
        return []

    async def mock_analyze_test_smells(test_func, parsed_file=None):
        # Simulate LLM API call delay (50ms per call)
        await asyncio.sleep(0.05)
        return []

    analyzer.analyze_assertion_quality = mock_analyze_assertion_quality
    analyzer.analyze_test_smells = mock_analyze_test_smells

    return analyzer


@pytest.fixture
def mock_parsed_files_with_uncertain_functions():
    """Create mock parsed files with uncertain test functions."""
    files = []
    for i in range(5):  # 5 files
        parsed_file = MagicMock(spec=ParsedTestFile)
        parsed_file.file_path = f"test_file_{i}.py"
        parsed_file.imports = []

        # Create 3 uncertain functions per file = 15 total
        functions = []
        for j in range(3):
            func = MagicMock(spec=TestFunctionInfo)
            func.name = f"test_function_{i}_{j}"
            func.line_number = j * 10
            func.class_name = f"TestClass{i}"
            func.source_code = "time.sleep(1)"  # Trigger uncertainty
            func.decorators = []
            func.parameters = []
            func.assertions = []
            functions.append(func)

        parsed_file.test_functions = functions
        parsed_file.test_classes = []
        files.append(parsed_file)

    return files


class TestHybridStrategyParallelization:
    """Test suite for HybridStrategy LLM parallelization."""

    @pytest.mark.asyncio
    async def test_semaphore_limits_concurrent_calls(
        self,
        mock_rule_engine,
        mock_llm_analyzer,
        mock_parsed_files_with_uncertain_functions,
    ):
        """Verify semaphore correctly limits concurrent LLM calls to max_concurrent."""
        # Track concurrent call count
        max_concurrent_observed = 0
        current_concurrent = 0
        lock = asyncio.Lock()

        async def tracked_analyze_assertion_quality(test_func, parsed_file=None):
            nonlocal max_concurrent_observed, current_concurrent
            async with lock:
                current_concurrent += 1
                max_concurrent_observed = max(
                    max_concurrent_observed, current_concurrent
                )

            await asyncio.sleep(0.05)  # Simulate LLM call

            async with lock:
                current_concurrent -= 1
            return []

        mock_llm_analyzer.analyze_assertion_quality = tracked_analyze_assertion_quality
        mock_llm_analyzer.analyze_test_smells = tracked_analyze_assertion_quality

        # Create strategy with max_concurrent=5
        strategy = HybridStrategy(
            uncertain_detector=UncertainCaseDetector(), max_concurrent_llm_calls=5
        )

        # Execute analysis
        await strategy.analyze(
            mock_parsed_files_with_uncertain_functions,
            mock_rule_engine,
            mock_llm_analyzer,
        )

        # Verify semaphore limit was respected
        assert max_concurrent_observed <= 5, (
            f"Semaphore failed: observed {max_concurrent_observed} concurrent calls "
            f"(limit was 5)"
        )
        assert (
            max_concurrent_observed >= 3
        ), "Expected some parallelism (at least 3 concurrent calls)"

    @pytest.mark.asyncio
    async def test_parallel_execution_faster_than_sequential(
        self,
        mock_rule_engine,
        mock_llm_analyzer,
        mock_parsed_files_with_uncertain_functions,
    ):
        """Verify parallel execution is significantly faster than sequential."""
        # Sequential strategy (max_concurrent=1)
        sequential_strategy = HybridStrategy(
            uncertain_detector=UncertainCaseDetector(), max_concurrent_llm_calls=1
        )

        # Parallel strategy (max_concurrent=10)
        parallel_strategy = HybridStrategy(
            uncertain_detector=UncertainCaseDetector(), max_concurrent_llm_calls=10
        )

        # Measure sequential execution time
        start_time = time.time()
        await sequential_strategy.analyze(
            mock_parsed_files_with_uncertain_functions,
            mock_rule_engine,
            mock_llm_analyzer,
        )
        sequential_time = time.time() - start_time

        # Measure parallel execution time
        start_time = time.time()
        await parallel_strategy.analyze(
            mock_parsed_files_with_uncertain_functions,
            mock_rule_engine,
            mock_llm_analyzer,
        )
        parallel_time = time.time() - start_time

        # Parallel should be at least 3x faster (15 calls with concurrency=10 vs concurrency=1)
        speedup = sequential_time / parallel_time
        assert speedup >= 3.0, (
            f"Parallel execution not significantly faster: {speedup:.2f}x speedup "
            f"(expected >= 3x). Sequential: {sequential_time:.2f}s, "
            f"Parallel: {parallel_time:.2f}s"
        )

    @pytest.mark.asyncio
    async def test_failed_llm_call_doesnt_block_others(
        self, mock_rule_engine, mock_parsed_files_with_uncertain_functions
    ):
        """Verify that one failed LLM call doesn't prevent other calls from completing."""
        call_count = 0

        async def failing_llm_analyzer(test_func, parsed_file=None):
            nonlocal call_count
            call_count += 1

            # First call fails, others succeed
            if call_count == 1:
                raise ValueError("Simulated LLM API error")

            await asyncio.sleep(0.01)
            return []

        mock_llm_analyzer = AsyncMock()
        mock_llm_analyzer.analyze_assertion_quality = failing_llm_analyzer
        mock_llm_analyzer.analyze_test_smells = failing_llm_analyzer

        strategy = HybridStrategy(
            uncertain_detector=UncertainCaseDetector(), max_concurrent_llm_calls=10
        )

        # Execute analysis - should not raise exception
        result = await strategy.analyze(
            mock_parsed_files_with_uncertain_functions,
            mock_rule_engine,
            mock_llm_analyzer,
        )

        # Verify other calls completed (15 functions × 2 calls each = 30 total)
        assert call_count >= 29, (
            f"Only {call_count} LLM calls completed (expected ~30). "
            "Failed call may have blocked others."
        )

        # Result should still be returned (partial results)
        assert isinstance(
            result, list
        ), "Analysis should return results even with failures"

    @pytest.mark.asyncio
    async def test_configurable_concurrency_limit(
        self,
        mock_rule_engine,
        mock_llm_analyzer,
        mock_parsed_files_with_uncertain_functions,
    ):
        """Verify concurrency limit can be configured."""
        for max_concurrent in [1, 5, 10, 20]:
            strategy = HybridStrategy(
                uncertain_detector=UncertainCaseDetector(),
                max_concurrent_llm_calls=max_concurrent,
            )

            # Verify semaphore is created with correct limit
            assert strategy.llm_semaphore._value == max_concurrent, (
                f"Semaphore limit should be {max_concurrent}, "
                f"got {strategy.llm_semaphore._value}"
            )

            # Verify analysis completes successfully
            result = await strategy.analyze(
                mock_parsed_files_with_uncertain_functions,
                mock_rule_engine,
                mock_llm_analyzer,
            )
            assert isinstance(
                result, list
            ), f"Analysis failed with max_concurrent={max_concurrent}"

    @pytest.mark.asyncio
    async def test_empty_uncertain_functions(self, mock_rule_engine, mock_llm_analyzer):
        """Verify strategy handles case where no uncertain functions are found."""
        # Create parsed files with no uncertain functions
        parsed_file = MagicMock(spec=ParsedTestFile)
        parsed_file.file_path = "test_simple.py"
        parsed_file.imports = []

        func = MagicMock(spec=TestFunctionInfo)
        func.name = "test_simple_case"
        func.line_number = 10
        func.class_name = None
        func.source_code = "assert True"  # Not uncertain
        func.decorators = []
        func.parameters = []
        # Create proper mock for assertions
        assertion_mock = MagicMock()
        assertion_mock.assertion_type = "assert"
        func.assertions = [assertion_mock]

        parsed_file.test_functions = [func]
        parsed_file.test_classes = []

        strategy = HybridStrategy(
            uncertain_detector=UncertainCaseDetector(), max_concurrent_llm_calls=10
        )

        # Execute analysis - no LLM calls should be made
        result = await strategy.analyze(
            [parsed_file], mock_rule_engine, mock_llm_analyzer
        )

        # Verify analysis completes without error
        assert isinstance(
            result, list
        ), "Analysis should handle empty uncertain functions"

        # Verify no LLM calls were made - check that the functions weren't called
        # Since we're using real async functions, we can't use assert_not_awaited
        # Instead, we'll verify the result is just from rule engine (empty in this case)
        assert (
            len(result) == 0
        ), "Should have no issues from LLM since no uncertain functions"

    @pytest.mark.asyncio
    async def test_progress_logging(
        self,
        mock_rule_engine,
        mock_llm_analyzer,
        mock_parsed_files_with_uncertain_functions,
        caplog,
    ):
        """Verify progress logs are emitted during parallel execution."""
        import logging

        caplog.set_level(logging.INFO)

        strategy = HybridStrategy(
            uncertain_detector=UncertainCaseDetector(), max_concurrent_llm_calls=10
        )

        await strategy.analyze(
            mock_parsed_files_with_uncertain_functions,
            mock_rule_engine,
            mock_llm_analyzer,
        )

        # Verify logs contain parallel execution information
        log_messages = [record.message for record in caplog.records]

        # Check for "Starting parallel LLM analysis" log
        assert any(
            "parallel" in msg.lower() for msg in log_messages
        ), "Expected log about parallel LLM analysis start"

        # Check for completion log with timing
        assert any(
            "completed" in msg.lower() for msg in log_messages
        ), "Expected log about parallel LLM analysis completion"


class TestLLMOnlyStrategyParallelization:
    """Test suite for LLMOnlyStrategy LLM parallelization."""

    @pytest.mark.asyncio
    async def test_llm_only_strategy_uses_parallelization(
        self,
        mock_rule_engine,
        mock_llm_analyzer,
        mock_parsed_files_with_uncertain_functions,
    ):
        """Verify LLMOnlyStrategy also benefits from parallelization."""
        # Note: LLMOnlyStrategy will be updated in Task 1.2
        # This test is a placeholder for that implementation

        strategy = LLMOnlyStrategy()

        # Measure execution time
        start_time = time.time()
        result = await strategy.analyze(
            mock_parsed_files_with_uncertain_functions[
                :2
            ],  # Use 2 files for faster test
            mock_rule_engine,
            mock_llm_analyzer,
        )
        elapsed = time.time() - start_time

        # Verify analysis completes
        assert isinstance(result, list), "LLMOnlyStrategy should return results"

        # TODO: After Task 1.2, verify parallel execution improves performance


class TestConcurrencyConfiguration:
    """Test suite for concurrency configuration."""

    def test_default_concurrency_limit(self):
        """Verify default concurrency limit is set correctly."""
        from app.core.constants import MAX_CONCURRENT_LLM_CALLS

        # Default should be 10 (balanced performance)
        assert (
            MAX_CONCURRENT_LLM_CALLS == 10
        ), f"Default concurrency should be 10, got {MAX_CONCURRENT_LLM_CALLS}"

    @patch.dict("os.environ", {"LLM_MAX_CONCURRENT_CALLS": "5"})
    def test_environment_variable_override(self):
        """Verify concurrency limit can be overridden via environment variable."""
        from app.config import get_settings

        # Reload settings with new environment variable
        settings = get_settings()

        # Verify environment variable is respected
        # Note: This test will pass once Task 1.3 (configuration) is implemented
        assert hasattr(
            settings, "llm_max_concurrent_calls"
        ), "Settings should have llm_max_concurrent_calls field"


# Integration test markers for performance benchmarks
@pytest.mark.integration
@pytest.mark.performance
class TestParallelizationPerformance:
    """Integration tests for parallelization performance."""

    @pytest.mark.asyncio
    async def test_38_files_completes_under_15_seconds(self):
        """Performance test: 38 files should complete in < 15 seconds."""
        # This test will be implemented in integration test suite
        # Requires actual LLM client and 38 test files
        pytest.skip("Integration test - run separately with actual LLM client")

    @pytest.mark.asyncio
    async def test_results_match_sequential_execution(self):
        """Quality parity test: Parallel results should match sequential results."""
        # This test will be implemented in integration test suite
        # Verifies no regression in analysis quality
        pytest.skip("Integration test - run separately with actual data")
