"""Batch quality analysis service for Feature 4.

This module provides QualityAnalysisService which handles batch analysis
of multiple test files for quality issues with fix suggestions.
"""

import logging
import time
import uuid
from typing import TYPE_CHECKING, Dict, List, Optional

from app.analyzers.rule_engine import RuleEngine
from app.api.v1.schemas import (
    FileInput,
    FixSuggestion,
    QualityAnalysisResponse,
    QualityIssue,
    QualitySummary,
)
from app.core.analysis.llm_analyzer import LLMAnalyzer
from app.core.analyzer import TestAnalyzer
from app.core.llm.llm_client import create_llm_client

if TYPE_CHECKING:
    from app.core.graph.graph_service import GraphService

logger = logging.getLogger(__name__)


class QualityAnalysisService:
    """Service for batch quality analysis of test files.

    This service provides a simplified interface for analyzing multiple
    test files and returning quality issues with fix suggestions.

    Supports optional graph-based analysis for enhanced mock detection.
    """

    def __init__(
        self,
        test_analyzer: Optional[TestAnalyzer] = None,
        graph_service: Optional["GraphService"] = None,
        project_id: Optional[str] = None,
    ):
        """
        Initialize the quality analysis service.

        Args:
            test_analyzer: Optional TestAnalyzer instance (will create if None)
            graph_service: Optional GraphService for graph-based analysis
            project_id: Project identifier for graph queries
        """
        if test_analyzer is None:
            rule_engine = RuleEngine()
            llm_client = create_llm_client()
            llm_analyzer = LLMAnalyzer(llm_client)
            self.test_analyzer = TestAnalyzer(rule_engine, llm_analyzer)
        else:
            self.test_analyzer = test_analyzer

        self.graph_service = graph_service
        self.project_id = project_id

    async def analyze_batch(
        self, files: List[FileInput], mode: str = "hybrid"
    ) -> QualityAnalysisResponse:
        """
        Analyze multiple test files for quality issues.

        This method orchestrates the analysis of multiple files and converts
        the results to the Feature 4 Quality Analysis format.

        If GraphService is configured, it will fetch dependency data from
        the graph database to enhance mock detection accuracy.

        Args:
            files: List of test files to analyze
            mode: Analysis mode - "fast" (rules-only), "deep" (llm-only), or "hybrid"

        Returns:
            QualityAnalysisResponse with issues and summary

        Raises:
            ValueError: If files are empty or mode is invalid
        """
        if not files:
            raise ValueError("No files provided for analysis")

        start_time = time.time()
        analysis_id = str(uuid.uuid4())

        logger.info(
            "Starting quality analysis: analysis_id=%s, files=%d, mode=%s, graph_enabled=%s",
            analysis_id,
            len(files),
            mode,
            self.graph_service is not None,
        )
        logger.debug("Quality analysis files: %s", [f.path for f in files])

        try:
            # Step 1: Fetch dependency data from graph if available
            dependency_data = {}
            if self.graph_service and self.project_id:
                logger.debug("Fetching dependency data from graph database")
                dependency_data = await self._fetch_dependency_data(files)
                logger.debug(
                    "Fetched dependencies for %d test functions", len(dependency_data)
                )

            # Step 2: Inject dependency data into rule engine
            if dependency_data:
                self._inject_dependency_data(dependency_data)

            # Step 3: Convert mode to TestAnalyzer format
            analyzer_mode = self._convert_mode(mode)
            logger.debug("Converted mode: %s -> %s", mode, analyzer_mode)

            # Step 4: Perform analysis using existing TestAnalyzer
            logger.debug("Calling TestAnalyzer.analyze_files")
            analysis_result = await self.test_analyzer.analyze_files(
                files=files, mode=analyzer_mode
            )
            logger.debug(
                "TestAnalyzer returned %d raw issues", len(analysis_result.issues)
            )

            # Step 5: Convert results to Quality Analysis format
            logger.debug("Converting issues to quality analysis format")
            quality_issues = self._convert_issues(analysis_result.issues)

            # Step 6: Calculate summary statistics
            summary = self._calculate_summary(files, quality_issues)

            elapsed_ms = int((time.time() - start_time) * 1000)
            logger.info(
                "Quality analysis completed: analysis_id=%s, issues=%d, time_ms=%d",
                analysis_id,
                len(quality_issues),
                elapsed_ms,
            )

            return QualityAnalysisResponse(
                analysis_id=analysis_id, summary=summary, issues=quality_issues
            )

        except Exception as e:
            logger.error(
                "Quality analysis failed: analysis_id=%s, error=%s",
                analysis_id,
                e,
                exc_info=True,
            )
            raise

    async def _fetch_dependency_data(
        self, files: List[FileInput]
    ) -> Dict[str, List[str]]:
        """
        Fetch dependency data from graph database for test functions.

        Args:
            files: List of test files being analyzed

        Returns:
            Dictionary mapping test function names to their dependencies
            Example: {"test_save_user": ["save_to_db", "send_email"]}
        """
        dependency_data = {}

        try:
            for file_input in files:
                # Extract test function names from file path
                # We'll query the graph for each test function
                file_path = file_input.path

                # Query symbols in this file
                query = """
                MATCH (s:Symbol {project_id: $project_id, file_path: $file_path})
                WHERE s.name STARTS WITH 'test_' OR s.kind = 'method'
                OPTIONAL MATCH (s)-[:CALLS]->(callee:Symbol)
                RETURN s.name AS test_name, collect(callee.name) AS dependencies
                """

                result = await self.graph_service.client.execute_query(
                    query, {"project_id": self.project_id, "file_path": file_path}
                )

                for record in result:
                    test_name = record["test_name"]
                    deps = [d for d in record["dependencies"] if d is not None]
                    if deps:
                        dependency_data[test_name] = deps

        except Exception as e:
            logger.warning(
                "Failed to fetch dependency data from graph: %s. Falling back to AST analysis.",
                e,
            )
            # If graph query fails, return empty dict and fallback to AST

        return dependency_data

    def _inject_dependency_data(self, dependency_data: Dict[str, List[str]]) -> None:
        """
        Inject dependency data into the rule engine.

        Args:
            dependency_data: Dictionary mapping test function names to dependencies
        """
        if hasattr(self.test_analyzer, "rule_engine"):
            self.test_analyzer.rule_engine.set_graph_dependency_data(dependency_data)
            logger.debug("Injected dependency data into rule engine")

    def _convert_mode(self, mode: str) -> str:
        """
        Convert Feature 4 mode to TestAnalyzer mode.

        Args:
            mode: Feature 4 mode (fast/deep/hybrid)

        Returns:
            TestAnalyzer mode (rules-only/llm-only/hybrid)
        """
        mode_mapping = {
            "fast": "rules-only",
            "deep": "llm-only",
            "hybrid": "hybrid",
        }

        if mode not in mode_mapping:
            raise ValueError(
                f"Invalid mode: {mode}. Must be one of {list(mode_mapping.keys())}"
            )

        return mode_mapping[mode]

    def _convert_issues(self, issues: List) -> List[QualityIssue]:
        """
        Convert TestAnalyzer issues to QualityIssue format.

        Args:
            issues: Issues from TestAnalyzer

        Returns:
            List of QualityIssue objects
        """
        quality_issues = []

        for issue in issues:
            # Convert suggestion if present
            suggestion = None
            if hasattr(issue, "suggestion") and issue.suggestion is not None:
                suggestion = self._convert_suggestion(issue.suggestion)

            # Map detected_by field
            detected_by = "rule" if issue.detected_by == "rule_engine" else "llm"

            quality_issue = QualityIssue(
                file_path=issue.file,
                line=issue.line,
                column=issue.column,
                severity=issue.severity,
                code=issue.type,
                message=issue.message,
                detected_by=detected_by,
                suggestion=suggestion,
            )
            quality_issues.append(quality_issue)

        return quality_issues

    def _convert_suggestion(self, suggestion) -> FixSuggestion:
        """
        Convert IssueSuggestion to FixSuggestion format.

        Args:
            suggestion: IssueSuggestion from TestAnalyzer

        Returns:
            FixSuggestion object
        """
        # Map action types
        action_mapping = {
            "replace": "replace",
            "remove": "delete",
            "add": "insert",
        }

        fix_type = action_mapping.get(suggestion.action, "replace")

        # For insert/add operations, use new_code
        # For replace, show both old and new
        # For delete, old_code contains what to delete
        new_text = suggestion.new_code

        return FixSuggestion(
            type=fix_type,
            new_text=new_text,
            description=suggestion.explanation,
        )

    def _calculate_summary(
        self, files: List[FileInput], issues: List[QualityIssue]
    ) -> QualitySummary:
        """
        Calculate summary statistics for the analysis.

        Args:
            files: List of analyzed files
            issues: List of detected issues

        Returns:
            QualitySummary with statistics
        """
        total_files = len(files)
        total_issues = len(issues)
        critical_issues = len([issue for issue in issues if issue.severity == "error"])

        return QualitySummary(
            total_files=total_files,
            total_issues=total_issues,
            critical_issues=critical_issues,
        )

    async def close(self) -> None:
        """Close resources used by the service."""
        await self.test_analyzer.close()
