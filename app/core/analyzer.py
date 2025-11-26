"""Main analysis orchestrator for test code quality.

This module provides the main TestAnalyzer class that orchestrates
the entire analysis pipeline using a clean separation of concerns.
"""

import asyncio
import logging
import time
import uuid
from typing import TYPE_CHECKING, Dict, List, Optional

from app.analyzers.ast_parser import ParsedTestFile, parse_test_file
from app.api.v1.schemas import (
    AnalysisMetrics,
    AnalyzeResponse,
    FileInput,
    ImpactAnalysisResponse,
    ImpactItem,
)
from app.core.analysis.strategies import get_strategy
from app.core.protocols import LLMAnalyzerProtocol, RuleEngineProtocol

if TYPE_CHECKING:
    from app.core.graph.graph_service import GraphService

logger = logging.getLogger(__name__)


class TestAnalyzer:
    """Main orchestrator for test analysis.

    This class follows the Single Responsibility Principle by delegating
    specific concerns to specialized components:
    - File parsing: handled by parse_test_file
    - Analysis strategy: handled by AnalysisStrategy implementations
    - Issue aggregation: handled by IssueAggregator
    - Metrics calculation: handled by MetricsCalculator

    The analyzer's single responsibility is high-level orchestration.
    """

    def __init__(
        self,
        rule_engine: RuleEngineProtocol,
        llm_analyzer: LLMAnalyzerProtocol,
    ):
        """
        Initialize the test analyzer.

        Args:
            rule_engine: Rule-based analysis engine
            llm_analyzer: LLM-based analyzer
        """
        self.rule_engine = rule_engine
        self.llm_analyzer = llm_analyzer

    async def analyze_files(
        self,
        files: List[FileInput],
        mode: str = "hybrid",
        config: Optional[Dict] = None,
    ) -> AnalyzeResponse:
        """
        Analyze test files and return detected issues.

        This method orchestrates the analysis pipeline:
        1. Parse files into AST
        2. Execute analysis strategy based on mode
        3. Calculate metrics

        Args:
            files: List of test files to analyze
            mode: "rules-only" | "llm-only" | "hybrid"
            config: Optional configuration overrides

        Returns:
            AnalyzeResponse with issues and metrics

        Raises:
            ValueError: If mode is invalid or files are empty
        """
        if not files:
            raise ValueError("No files provided for analysis")

        start_time = time.time()
        analysis_id = str(uuid.uuid4())

        logger.info(
            "Starting analysis: analysis_id=%s, mode=%s, files=%d",
            analysis_id,
            mode,
            len(files),
        )
        logger.debug("Analysis ID: %s", analysis_id)

        try:
            # Step 1: Parse all files in parallel
            logger.debug("Parsing %d files in parallel", len(files))
            parsed_files = await self._parse_files_parallel(files)
            logger.debug(
                "Parsed files: %d successful, %d total",
                len(parsed_files),
                len(files),
            )

            # Step 2: Get and execute analysis strategy
            logger.debug("Using strategy: %s", mode)
            strategy = get_strategy(mode)
            all_issues = await strategy.analyze(
                parsed_files, self.rule_engine, self.llm_analyzer
            )

            # Step 3: Calculate metrics
            total_tests = self._count_total_tests(parsed_files)
            analysis_time_ms = int((time.time() - start_time) * 1000)
            metrics = AnalysisMetrics(
                total_tests=total_tests,
                issues_count=len(all_issues),
                analysis_time_ms=analysis_time_ms,
            )

            logger.info(
                "Analysis completed: analysis_id=%s, issues=%d, tests=%d, time_ms=%d",
                analysis_id,
                len(all_issues),
                total_tests,
                metrics.analysis_time_ms,
            )

            return AnalyzeResponse(
                analysis_id=analysis_id, issues=all_issues, metrics=metrics
            )

        except Exception as e:
            logger.error(
                "Analysis failed: analysis_id=%s, error=%s",
                analysis_id,
                e,
                exc_info=True,
            )
            raise

    async def _parse_files_parallel(
        self, files: List[FileInput]
    ) -> List[ParsedTestFile]:
        """
        Parse multiple files in parallel for improved performance.

        Args:
            files: List of file inputs to parse

        Returns:
            List of successfully parsed test files
        """
        logger.debug("Creating %d parse tasks for parallel execution", len(files))
        tasks = []
        for file_input in files:
            task = asyncio.create_task(self._parse_file_safe(file_input))
            tasks.append(task)

        parsed_files = await asyncio.gather(*tasks, return_exceptions=True)
        logger.debug("All parse tasks completed")

        # Filter out failed parses and exceptions
        valid_files = []
        error_count = 0
        syntax_error_count = 0
        for i, result in enumerate(parsed_files):
            if isinstance(result, Exception):
                error_count += 1
                logger.error("Failed to parse file %s: %s", files[i].path, result)
            elif result.has_syntax_errors:
                syntax_error_count += 1
                logger.warning(
                    "File has syntax errors: path=%s, error=%s",
                    files[i].path,
                    result.syntax_error_message,
                )
                valid_files.append(result)
            else:
                valid_files.append(result)

        logger.debug(
            "Parse summary: %d valid, %d syntax_errors, %d failed",
            len(valid_files) - syntax_error_count,
            syntax_error_count,
            error_count,
        )

        return valid_files

    async def _parse_file_safe(self, file_input: FileInput) -> ParsedTestFile:
        """
        Safely parse a single file with error handling.

        Args:
            file_input: File input to parse

        Returns:
            Parsed test file (with error flags set if parsing failed)
        """
        try:
            return parse_test_file(file_input.path, file_input.content)
        except Exception as e:
            logger.error(f"Error parsing file {file_input.path}: {e}")
            # Return a file with syntax errors marked
            return ParsedTestFile(
                file_path=file_input.path,
                imports=[],
                fixtures=[],
                test_functions=[],
                test_classes=[],
                has_syntax_errors=True,
                syntax_error_message=str(e),
            )

    async def close(self) -> None:
        """Close the analyzer and cleanup resources."""
        await self.llm_analyzer.close()

    def _count_total_tests(self, parsed_files: List[ParsedTestFile]) -> int:
        """
        Count total number of test functions across all files.

        Args:
            parsed_files: List of parsed test files

        Returns:
            Total number of test functions
        """
        total_tests = 0

        for parsed_file in parsed_files:
            # Count module-level test functions
            total_tests += len(parsed_file.test_functions)

            # Count test methods in test classes
            for test_class in parsed_file.test_classes:
                total_tests += len(test_class.methods)

        return total_tests


class ImpactAnalyzer:
    """Impact analysis analyzer for determining affected test files.

    This analyzer takes project context (changed files and related tests)
    and determines which tests may be impacted by the changes using
    graph-based dependency analysis.
    """

    def __init__(
        self,
        rule_engine: RuleEngineProtocol,
        llm_analyzer: LLMAnalyzerProtocol,
        graph_service: Optional["GraphService"] = None,
        project_id: str = "default",
    ):
        """
        Initialize the impact analyzer.

        Args:
            rule_engine: Rule-based analysis engine
            llm_analyzer: LLM-based analyzer (for future enhancement)
            graph_service: Optional GraphService for dependency queries
            project_id: Project identifier for graph queries
        """
        self.rule_engine = rule_engine
        self.llm_analyzer = llm_analyzer
        self.graph_service = graph_service
        self.project_id = project_id

    def analyze_impact(
        self, files_changed: List[Dict[str, str]], related_tests: List[str]
    ) -> ImpactAnalysisResponse:
        """
        Analyze the impact of file changes on test files (sync wrapper).

        This method is kept for backward compatibility. For graph-based
        analysis, use analyze_impact_async instead.

        Args:
            files_changed: List of dictionaries with 'path' and 'change_type'
            related_tests: List of test file paths that may be related

        Returns:
            ImpactAnalysisResponse with impact assessment

        Raises:
            ValueError: If files_changed is empty
            RuntimeError: If graph_service is configured but async context unavailable
        """
        if self.graph_service is not None:
            raise RuntimeError(
                "ImpactAnalyzer has graph_service configured. "
                "Use analyze_impact_async() instead for graph-based analysis."
            )

        return self._analyze_impact_sync(files_changed, related_tests)

    async def analyze_impact_async(
        self,
        files_changed: List[Dict[str, str]],
        related_tests: List[str],
        git_diff: Optional[str] = None,
    ) -> ImpactAnalysisResponse:
        """
        Analyze the impact of file changes using graph-based dependency analysis.

        This method uses the Neo4j graph database to find reverse dependencies
        (functions that call the modified functions) for accurate impact assessment.

        Args:
            files_changed: List of dictionaries with 'path' and 'change_type'
            related_tests: List of test file paths that may be related
            git_diff: Optional git diff content for function-level analysis

        Returns:
            ImpactAnalysisResponse with impact assessment

        Raises:
            ValueError: If files_changed is empty
            RuntimeError: If graph_service is not configured
        """
        if self.graph_service is None:
            raise RuntimeError(
                "graph_service is required for analyze_impact_async(). "
                "Either configure graph_service or use analyze_impact() instead."
            )

        if not files_changed:
            raise ValueError("files_changed cannot be empty")

        changed_paths = [f.get("path", "") for f in files_changed]
        if not any(changed_paths):
            raise ValueError("files_changed paths cannot be empty")

        logger.info(
            "Analyzing impact (graph-based) for %d changed files, project=%s",
            len(files_changed),
            self.project_id,
        )

        try:
            impacted_tests = await self._calculate_impact_graph_based(
                files_changed, related_tests, git_diff
            )

            severity, suggested_action = self._determine_severity_and_action(
                impacted_tests
            )

            logger.info(
                "Impact analysis completed: %d tests impacted, severity=%s, action=%s",
                len(impacted_tests),
                severity,
                suggested_action,
            )

            return ImpactAnalysisResponse(
                impacted_tests=impacted_tests,
                severity=severity,
                suggested_action=suggested_action,
            )

        except Exception as e:
            logger.error("Impact analysis failed: %s", e, exc_info=True)
            raise

    def _analyze_impact_sync(
        self, files_changed: List[Dict[str, str]], related_tests: List[str]
    ) -> ImpactAnalysisResponse:
        """Synchronous impact analysis using heuristics (legacy method)."""
        if not files_changed:
            raise ValueError("files_changed cannot be empty")

        changed_paths = [f.get("path", "") for f in files_changed]
        if not any(changed_paths):
            raise ValueError("files_changed paths cannot be empty")

        logger.info(
            "Analyzing impact (heuristic) for %d changed files and %d related tests",
            len(files_changed),
            len(related_tests),
        )

        try:
            impacted_tests = self._calculate_impact_simple(changed_paths, related_tests)

            severity, suggested_action = self._determine_severity_and_action(
                impacted_tests
            )

            logger.info(
                "Impact analysis completed: %d tests impacted, severity=%s, action=%s",
                len(impacted_tests),
                severity,
                suggested_action,
            )

            return ImpactAnalysisResponse(
                impacted_tests=impacted_tests,
                severity=severity,
                suggested_action=suggested_action,
            )

        except Exception as e:
            logger.error("Impact analysis failed: %s", e)
            raise

    async def _calculate_impact_graph_based(
        self,
        files_changed: List[Dict[str, str]],
        related_tests: List[str],
        git_diff: Optional[str] = None,
    ) -> List[ImpactItem]:
        """
        Calculate impact using graph-based reverse dependency analysis.

        This method queries the Neo4j graph to find all functions that call
        the modified functions, allowing precise impact assessment.

        Enhanced to classify changes as functional vs non-functional.

        Args:
            files_changed: List of changed files with paths
            related_tests: List of potentially related test files
            git_diff: Optional git diff for function-level extraction

        Returns:
            List of ImpactItem with graph-based impact assessments
        """
        impacted_tests: List[ImpactItem] = []
        processed_test_paths: set = set()
        changed_paths = [f.get("path", "") for f in files_changed]

        # Extract AND classify changes from git diff if provided
        functional_changes = []
        non_functional_changes = []

        if git_diff:
            from app.core.utils.diff_parser import (
                extract_and_classify_modified_functions,
            )

            classified_changes = extract_and_classify_modified_functions(
                git_diff, use_ast=True  # Hybrid mode
            )

            logger.debug(
                "Classified %d changes: %d functional, %d non-functional, %d mixed",
                len(classified_changes),
                sum(1 for c in classified_changes if c.change_type == "functional"),
                sum(1 for c in classified_changes if c.change_type == "non-functional"),
                sum(1 for c in classified_changes if c.change_type == "mixed"),
            )

            # Separate functional and non-functional changes
            # Treat "mixed" as functional for safety
            functional_changes = [
                c
                for c in classified_changes
                if c.change_type in ["functional", "mixed"]
            ]
            non_functional_changes = [
                c for c in classified_changes if c.change_type == "non-functional"
            ]

        # Process FUNCTIONAL changes with graph queries
        for change in functional_changes:
            func_name = change.function_name
            try:
                result = await self.graph_service.query_reverse_dependencies(
                    function_name=func_name,
                    project_id=self.project_id,
                )

                if result["function"] is None:
                    logger.debug("Function %s not found in graph", func_name)
                    continue

                # Process callers - each caller might be a test or call from a test
                for caller in result["callers"]:
                    caller_path = caller.get("file_path", "")
                    caller_name = caller.get("name", "")

                    # Check if caller is in a test file
                    is_test_file = (
                        "test" in caller_path.lower()
                        or caller_path.endswith("_test.py")
                        or caller_name.startswith("test_")
                    )

                    if is_test_file and caller_path not in processed_test_paths:
                        impacted_tests.append(
                            ImpactItem(
                                test_path=caller_path,
                                impact_score=0.9,
                                severity="high",
                                reasons=[
                                    f"Test calls modified function '{func_name}' "
                                    f"(via graph analysis)"
                                ],
                            )
                        )
                        processed_test_paths.add(caller_path)
                    elif not is_test_file:
                        # Caller is not a test - need to check if any test calls this caller
                        # This handles transitive dependencies
                        transitive_result = (
                            await self.graph_service.query_reverse_dependencies(
                                function_name=caller_name,
                                project_id=self.project_id,
                            )
                        )

                        for transitive_caller in transitive_result.get("callers", []):
                            trans_path = transitive_caller.get("file_path", "")
                            trans_name = transitive_caller.get("name", "")

                            is_trans_test = (
                                "test" in trans_path.lower()
                                or trans_path.endswith("_test.py")
                                or trans_name.startswith("test_")
                            )

                            if is_trans_test and trans_path not in processed_test_paths:
                                impacted_tests.append(
                                    ImpactItem(
                                        test_path=trans_path,
                                        impact_score=0.7,
                                        severity="medium",
                                        reasons=[
                                            f"Test calls '{caller_name}' which calls "
                                            f"modified function '{func_name}' "
                                            f"(transitive dependency)"
                                        ],
                                    )
                                )
                                processed_test_paths.add(trans_path)

            except Exception as e:
                logger.warning(
                    "Failed to query reverse dependencies for %s: %s",
                    func_name,
                    e,
                )

        # Process NON-FUNCTIONAL changes (mark as informational, no graph queries)
        for change in non_functional_changes:
            # Infer corresponding test file
            test_path = self._infer_test_path_from_file(change.file_path)

            if test_path and test_path not in processed_test_paths:
                impacted_tests.append(
                    ImpactItem(
                        test_path=test_path,
                        impact_score=0.1,  # Very low impact
                        severity="informational",
                        reasons=[
                            f"Non-functional change in {change.function_name}: "
                            f"{', '.join(change.reasons)}"
                        ],
                    )
                )
                processed_test_paths.add(test_path)

        # Also check for direct test file modifications
        for changed_path in changed_paths:
            is_test_file = "test" in changed_path.lower() or changed_path.endswith(
                "_test.py"
            )

            if is_test_file and changed_path not in processed_test_paths:
                impacted_tests.append(
                    ImpactItem(
                        test_path=changed_path,
                        impact_score=1.0,
                        severity="high",
                        reasons=["Test file was directly modified"],
                    )
                )
                processed_test_paths.add(changed_path)

        # Add related tests that weren't found via graph with lower scores
        for test_path in related_tests:
            if test_path not in processed_test_paths:
                impacted_tests.append(
                    ImpactItem(
                        test_path=test_path,
                        impact_score=0.3,
                        severity="low",
                        reasons=["Related test (no direct dependency found in graph)"],
                    )
                )
                processed_test_paths.add(test_path)

        logger.info(
            "Graph-based impact analysis found %d impacted tests",
            len(impacted_tests),
        )

        return impacted_tests

    def _infer_test_path_from_file(self, source_file: str) -> Optional[str]:
        """
        Infer corresponding test file path from source file.

        Uses common test file naming conventions to map source files to tests.

        Args:
            source_file: Path to source file (e.g., "src/calculator.py")

        Returns:
            Inferred test file path (e.g., "tests/test_calculator.py"),
            or None if cannot infer

        Examples:
            >>> self._infer_test_path_from_file("src/calculator.py")
            "tests/test_calculator.py"
            >>> self._infer_test_path_from_file("app/utils/helper.py")
            "tests/test_helper.py"
        """
        # If already a test file, return it
        if "test" in source_file.lower():
            return source_file

        # Extract filename from path
        parts = source_file.split("/")
        filename = parts[-1]

        # Create test filename
        if filename.endswith(".py"):
            name_without_ext = filename[:-3]
            test_filename = f"test_{name_without_ext}.py"
        else:
            return None

        # Common test directory patterns
        test_patterns = [
            f"tests/{test_filename}",
            f"test/{test_filename}",
        ]

        # Try to construct relative path
        # e.g., src/module/file.py -> tests/module/test_file.py
        if len(parts) > 1:
            # Try to preserve directory structure under tests/
            subpath = "/".join(parts[1:-1]) if len(parts) > 2 else ""
            if subpath:
                test_patterns.insert(0, f"tests/{subpath}/{test_filename}")

        # Return first pattern (could be enhanced to check file existence)
        return test_patterns[0] if test_patterns else None

    def _calculate_impact_simple(
        self, changed_paths: List[str], related_tests: List[str]
    ) -> List[ImpactItem]:
        """
        Simple heuristic-based impact calculation.

        This is a placeholder implementation that will be enhanced later
        with rule engine and LLM capabilities.

        Args:
            changed_paths: List of changed file paths
            related_tests: List of potentially related test files

        Returns:
            List of ImpactItem with impact assessments
        """
        impacted_tests = []
        # Use a set for O(1) lookup to avoid O(n^2) complexity
        processed_test_paths = set()

        # Simple heuristics:
        # 1. If a test file is in the changed files, it's definitely impacted
        # 2. If a test file name matches a changed file (e.g., test_*.py vs *.py), it's likely impacted
        # 3. If no clear relationship, assign low impact

        # Combine changed paths with related tests for analysis
        all_test_candidates = list(related_tests)

        for changed_path in changed_paths:
            # Extract filename without extension
            changed_name = changed_path.split("/")[-1].split(".")[0]

            # If this is a test file, mark it as impacted
            if "test" in changed_path.lower() or changed_path.endswith(("_test.py",)):
                # Also check for test_*.py pattern using startswith
                test_file_pattern = (
                    changed_path.lower().endswith(("_test.py",))
                    or changed_path.lower().startswith("test_")
                    or "_test" in changed_path.lower()
                )
                if test_file_pattern or "test" in changed_path.lower():
                    impacted_tests.append(
                        ImpactItem(
                            test_path=changed_path,
                            impact_score=1.0,
                            severity="high",
                            reasons=["Test file was directly modified"],
                        )
                    )
                    processed_test_paths.add(changed_path)
                    continue

            # Look for potentially related test files
            for test_path in all_test_candidates:
                if test_path not in processed_test_paths:
                    test_name = test_path.split("/")[-1].split(".")[0]

                    # Check for naming patterns (e.g., module.py -> test_module.py)
                    if (
                        test_name == f"test_{changed_name}"
                        or test_name == f"{changed_name}_test"
                        or changed_name in test_name
                    ):
                        impacted_tests.append(
                            ImpactItem(
                                test_path=test_path,
                                impact_score=0.8,
                                severity="high",
                                reasons=[
                                    f"Test file name matches changed file: {changed_path}"
                                ],
                            )
                        )
                        processed_test_paths.add(test_path)
                        # Add break to prevent checking this test file again on next iteration
                        break
                    elif (
                        changed_name.replace("_", "").lower()
                        in test_name.replace("_", "").lower()
                    ):
                        impacted_tests.append(
                            ImpactItem(
                                test_path=test_path,
                                impact_score=0.5,
                                severity="medium",
                                reasons=[
                                    f"Test file may be related to changed file: {changed_path}"
                                ],
                            )
                        )
                        processed_test_paths.add(test_path)
                        # Add break to prevent duplicate entries
                        break

        # Add any remaining related tests with low impact
        for test_path in related_tests:
            if test_path not in processed_test_paths:
                impacted_tests.append(
                    ImpactItem(
                        test_path=test_path,
                        impact_score=0.1,
                        severity="low",
                        reasons=["Test file in related tests but no clear connection"],
                    )
                )
                processed_test_paths.add(test_path)

        return impacted_tests

    def _determine_severity_and_action(
        self, impacted_tests: List[ImpactItem]
    ) -> tuple[str, str]:
        """
        Determine overall severity and suggested action based on impacts.

        Enhanced to handle informational severity for non-functional changes.

        Args:
            impacted_tests: List of impact items

        Returns:
            Tuple of (severity, suggested_action)
        """
        if not impacted_tests:
            return "none", "no-action"

        # Filter out informational impacts for severity calculation
        # Informational-only changes should not trigger test runs
        significant_tests = [
            t for t in impacted_tests if t.severity not in ["informational", "none"]
        ]

        # If only informational changes, return informational severity
        if not significant_tests:
            if any(t.severity == "informational" for t in impacted_tests):
                return "informational", "no-action"
            else:
                return "none", "no-action"

        # Check for high severity impacts among significant tests
        high_impact_tests = [it for it in significant_tests if it.severity == "high"]
        medium_impact_tests = [
            it for it in significant_tests if it.severity == "medium"
        ]

        if len(high_impact_tests) > 2:
            # Multiple high impact tests -> high severity, run all tests
            return "high", "run-all-tests"
        elif high_impact_tests or len(medium_impact_tests) > 3:
            # Some high impact or many medium impact -> medium severity
            return "medium", "run-affected-tests"
        else:
            # Only low impact tests -> low severity
            return "low", "run-affected-tests"
