"""Analysis strategy implementations.

This module implements the Strategy Pattern for different analysis modes,
enabling the Open/Closed Principle by making the system extensible without
modifying existing code.
"""

import logging
from typing import List

from app.analyzers.ast_parser import ParsedTestFile, TestFunctionInfo
from app.api.v1.schemas import Issue
from app.core.analysis.uncertain_case_detector import UncertainCaseDetector
from app.core.protocols import AnalysisStrategy, LLMAnalyzerProtocol, RuleEngineProtocol

logger = logging.getLogger(__name__)


class RulesOnlyStrategy(AnalysisStrategy):
    """Strategy that uses only rule-based analysis.

    This is the fastest strategy, suitable for quick checks and CI/CD pipelines.
    """

    async def analyze(
        self,
        parsed_files: List[ParsedTestFile],
        rule_engine: RuleEngineProtocol,
        llm_analyzer: LLMAnalyzerProtocol,
    ) -> List[Issue]:
        """
        Execute rule-based analysis only.

        Args:
            parsed_files: List of parsed test files
            rule_engine: Rule-based analysis engine
            llm_analyzer: LLM-based analyzer (not used in this strategy)

        Returns:
            List of detected issues from rule engine
        """
        logger.info("Starting rules-only analysis on %d files", len(parsed_files))
        rule_issues = []

        for parsed_file in parsed_files:
            try:
                logger.debug("Analyzing file with rules: %s", parsed_file.file_path)
                file_issues = rule_engine.analyze(parsed_file)
                rule_issues.extend(file_issues)
                logger.debug(
                    "Rules analysis completed: file=%s, issues=%d",
                    parsed_file.file_path,
                    len(file_issues),
                )
            except Exception as e:
                logger.error(
                    "Rule engine failed for file %s: %s",
                    parsed_file.file_path,
                    e,
                    exc_info=True,
                )

        logger.info("Rules-only analysis completed: total_issues=%d", len(rule_issues))
        return rule_issues

    def get_name(self) -> str:
        """Get the strategy name."""
        return "rules-only"


class LLMOnlyStrategy(AnalysisStrategy):
    """Strategy that uses only LLM-based analysis.

    This strategy provides deeper analysis but is slower and requires API access.
    """

    async def analyze(
        self,
        parsed_files: List[ParsedTestFile],
        rule_engine: RuleEngineProtocol,
        llm_analyzer: LLMAnalyzerProtocol,
    ) -> List[Issue]:
        """
        Execute LLM-based analysis only.

        Args:
            parsed_files: List of parsed test files
            rule_engine: Rule-based analysis engine (not used in this strategy)
            llm_analyzer: LLM-based analyzer

        Returns:
            List of detected issues from LLM analysis
        """
        logger.info("Starting LLM-only analysis on %d files", len(parsed_files))
        llm_issues = []

        for parsed_file in parsed_files:
            # Analyze all test functions with LLM
            logger.debug("Analyzing file with LLM: %s", parsed_file.file_path)
            file_issues = await self._analyze_file_with_llm(parsed_file, llm_analyzer)
            llm_issues.extend(file_issues)
            logger.debug(
                "LLM analysis completed: file=%s, issues=%d",
                parsed_file.file_path,
                len(file_issues),
            )

        logger.info("LLM-only analysis completed: total_issues=%d", len(llm_issues))
        return llm_issues

    async def _analyze_file_with_llm(
        self, parsed_file: ParsedTestFile, llm_analyzer: LLMAnalyzerProtocol
    ) -> List[Issue]:
        """
        Analyze entire file with LLM.

        Args:
            parsed_file: Parsed test file
            llm_analyzer: LLM-based analyzer

        Returns:
            List of detected issues
        """
        llm_issues = []

        # Analyze module-level functions
        for test_func in parsed_file.test_functions:
            func_issues = await self._analyze_function_with_llm(
                test_func, parsed_file, llm_analyzer
            )
            llm_issues.extend(func_issues)

        # Analyze test class methods
        for test_class in parsed_file.test_classes:
            for test_method in test_class.methods:
                method_issues = await self._analyze_function_with_llm(
                    test_method, parsed_file, llm_analyzer
                )
                llm_issues.extend(method_issues)

        return llm_issues

    async def _analyze_function_with_llm(
        self,
        test_func: TestFunctionInfo,
        parsed_file: ParsedTestFile,
        llm_analyzer: LLMAnalyzerProtocol,
    ) -> List[Issue]:
        """
        Analyze a single test function with LLM.

        Args:
            test_func: Test function to analyze
            parsed_file: Parsed test file context
            llm_analyzer: LLM-based analyzer

        Returns:
            List of detected issues
        """
        llm_issues = []

        try:
            # Analyze assertion quality
            quality_issues = await llm_analyzer.analyze_assertion_quality(
                test_func, parsed_file
            )
            llm_issues.extend(quality_issues)

            # Analyze test smells
            smell_issues = await llm_analyzer.analyze_test_smells(
                test_func, parsed_file
            )
            llm_issues.extend(smell_issues)

        except Exception as e:
            logger.error(f"LLM analysis failed for function {test_func.name}: {e}")

        return llm_issues

    def get_name(self) -> str:
        """Get the strategy name."""
        return "llm-only"


class HybridStrategy(AnalysisStrategy):
    """Strategy that combines rule-based and LLM-based analysis.

    This strategy uses fast rule-based checks for all tests, then applies
    LLM analysis only to uncertain cases that need deeper inspection.
    This provides a good balance between speed and comprehensiveness.

    Optimized to minimize LLM token consumption by using stricter
    uncertain case detection criteria.
    """

    def __init__(self):
        """Initialize hybrid strategy with uncertain case detector."""
        from app.core.constants import (
            MAX_LLM_CALLS_PER_FILE,
            MIN_ASSERTIONS_FOR_COMPLEX,
            MIN_DECORATORS_FOR_UNUSUAL,
            NAME_SIMILARITY_THRESHOLD,
        )

        self.uncertain_detector = UncertainCaseDetector(
            min_assertions_for_complex=MIN_ASSERTIONS_FOR_COMPLEX,
            min_decorators_for_unusual=MIN_DECORATORS_FOR_UNUSUAL,
            similarity_threshold=NAME_SIMILARITY_THRESHOLD,
            max_llm_calls_per_file=MAX_LLM_CALLS_PER_FILE,
        )

    async def analyze(
        self,
        parsed_files: List[ParsedTestFile],
        rule_engine: RuleEngineProtocol,
        llm_analyzer: LLMAnalyzerProtocol,
    ) -> List[Issue]:
        """
        Execute hybrid analysis (rules + LLM for uncertain cases).

        Args:
            parsed_files: List of parsed test files
            rule_engine: Rule-based analysis engine
            llm_analyzer: LLM-based analyzer

        Returns:
            List of detected issues from both analyses
        """
        logger.info("Starting hybrid analysis on %d files", len(parsed_files))
        all_issues = []

        # Step 1: Run rule engine analysis (fast, always runs)
        logger.debug("Phase 1: Running rules-only analysis on all files")
        rules_issues_count = 0
        for parsed_file in parsed_files:
            try:
                file_issues = rule_engine.analyze(parsed_file)
                all_issues.extend(file_issues)
                rules_issues_count += len(file_issues)
            except Exception as e:
                logger.error(
                    "Rule engine failed for file %s: %s",
                    parsed_file.file_path,
                    e,
                    exc_info=True,
                )

        logger.debug("Phase 1 completed: %d issues from rules", rules_issues_count)

        # Step 2: Run LLM analysis only on uncertain cases
        logger.debug("Phase 2: Identifying uncertain cases for LLM analysis")
        total_uncertain = 0
        llm_issues_count = 0
        for parsed_file in parsed_files:
            uncertain_functions = self.uncertain_detector.identify_uncertain_cases(
                parsed_file
            )
            total_uncertain += len(uncertain_functions)

            for test_func in uncertain_functions:
                func_issues = await self._analyze_function_with_llm(
                    test_func, parsed_file, llm_analyzer
                )
                all_issues.extend(func_issues)
                llm_issues_count += len(func_issues)

        logger.debug(
            "Phase 2 completed: %d uncertain cases analyzed, %d issues from LLM",
            total_uncertain,
            llm_issues_count,
        )
        logger.info(
            "Hybrid analysis completed: total_issues=%d (rules=%d, llm=%d)",
            len(all_issues),
            rules_issues_count,
            llm_issues_count,
        )

        return all_issues

    async def _analyze_function_with_llm(
        self,
        test_func: TestFunctionInfo,
        parsed_file: ParsedTestFile,
        llm_analyzer: LLMAnalyzerProtocol,
    ) -> List[Issue]:
        """
        Analyze a single test function with LLM.

        Args:
            test_func: Test function to analyze
            parsed_file: Parsed test file context
            llm_analyzer: LLM-based analyzer

        Returns:
            List of detected issues
        """
        llm_issues = []

        try:
            # Analyze assertion quality
            quality_issues = await llm_analyzer.analyze_assertion_quality(
                test_func, parsed_file
            )
            llm_issues.extend(quality_issues)

            # Analyze test smells
            smell_issues = await llm_analyzer.analyze_test_smells(
                test_func, parsed_file
            )
            llm_issues.extend(smell_issues)

        except Exception as e:
            logger.error(f"LLM analysis failed for function {test_func.name}: {e}")

        return llm_issues

    def get_name(self) -> str:
        """Get the strategy name."""
        return "hybrid"


# Strategy registry for easy lookup
STRATEGY_REGISTRY = {
    "rules-only": RulesOnlyStrategy,
    "llm-only": LLMOnlyStrategy,
    "hybrid": HybridStrategy,
}


def get_strategy(mode: str) -> AnalysisStrategy:
    """
    Get analysis strategy by mode name.

    This factory function enables easy extension with new strategies
    without modifying existing code.

    Args:
        mode: Analysis mode name

    Returns:
        Analysis strategy instance

    Raises:
        ValueError: If mode is not recognized
    """
    strategy_class = STRATEGY_REGISTRY.get(mode)
    if strategy_class is None:
        valid_modes = ", ".join(STRATEGY_REGISTRY.keys())
        raise ValueError(f"Invalid analysis mode '{mode}'. Valid modes: {valid_modes}")

    return strategy_class()
