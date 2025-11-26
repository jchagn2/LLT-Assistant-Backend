"""Optimized uncertain case detector with stricter criteria.

This version significantly reduces false positives to minimize LLM token usage
while still catching truly problematic test cases.
"""

from typing import List

from app.analyzers.ast_parser import ParsedTestFile, TestFunctionInfo


class UncertainCaseDetector:
    """Identifies test functions that need LLM analysis in hybrid mode."""

    def __init__(
        self,
        min_assertions_for_complex: int = 5,  # Increased from 3
        min_decorators_for_unusual: int = 4,  # Increased from 3
        similarity_threshold: float = 0.75,  # More strict similarity
        max_llm_calls_per_file: int = 5,  # Limit LLM calls per file
    ):
        """
        Initialize detector with configurable thresholds.

        Args:
            min_assertions_for_complex: Minimum assertions to consider complex
            min_decorators_for_unusual: Minimum decorators to consider unusual
            similarity_threshold: Name similarity threshold (0-1)
            max_llm_calls_per_file: Maximum uncertain tests per file
        """
        self.min_assertions = min_assertions_for_complex
        self.min_decorators = min_decorators_for_unusual
        self.similarity_threshold = similarity_threshold
        self.max_llm_calls = max_llm_calls_per_file

    def identify_uncertain_cases(
        self, parsed_file: ParsedTestFile
    ) -> List[TestFunctionInfo]:
        """
        Identify test functions that need LLM analysis in hybrid mode.

        Uses stricter criteria to reduce false positives and token consumption.

        Criteria (in priority order):
        1. Test smells (sleep, global state) - highest priority
        2. Complex assertions (>5 assertions) or unusual decorator patterns (>4 decorators)
        3. Similar function names (potential merge candidates)

        Args:
            parsed_file: Parsed test file to analyze

        Returns:
            List of test functions that need LLM analysis (limited by max_llm_calls)
        """
        # Priority-based uncertain function detection
        high_priority = []
        medium_priority = []
        low_priority = []

        # Get all test functions
        all_functions = list(parsed_file.test_functions)
        for test_class in parsed_file.test_classes:
            all_functions.extend(test_class.methods)

        # Use sets of function IDs to track which functions are already categorized
        high_priority_ids = set()
        medium_priority_ids = set()

        # Priority 1: Test smells (most important)
        for func in all_functions:
            if self._has_test_smells(func):
                func_id = (func.name, func.line_number, func.class_name)
                high_priority_ids.add(func_id)
                high_priority.append(func)

        # Priority 2: Very complex assertions or unusual decorator patterns
        for func in all_functions:
            func_id = (func.name, func.line_number, func.class_name)
            if func_id not in high_priority_ids and (
                self._has_very_complex_assertions(func)
                or self._has_unusual_decorator_patterns(func)
            ):
                medium_priority_ids.add(func_id)
                medium_priority.append(func)

        # Priority 3: Similar names (only if very similar)
        similar_pairs = self._find_similar_function_pairs(all_functions)
        for func1, func2 in similar_pairs:
            func1_id = (func1.name, func1.line_number, func1.class_name)
            func2_id = (func2.name, func2.line_number, func2.class_name)

            if (
                func1_id not in high_priority_ids
                and func1_id not in medium_priority_ids
            ):
                low_priority.append(func1)
            if (
                func2_id not in high_priority_ids
                and func2_id not in medium_priority_ids
            ):
                low_priority.append(func2)

        # Combine with priority order and limit
        uncertain_functions = (
            high_priority
            + medium_priority[: max(0, self.max_llm_calls - len(high_priority))]
            + low_priority[
                : max(
                    0,
                    self.max_llm_calls - len(high_priority) - len(medium_priority),
                )
            ]
        )

        # Remove duplicates while preserving order
        # Use (name, line_number, class_name) as unique identifier instead of the object itself
        seen = set()
        result = []
        for func in uncertain_functions:
            func_id = (func.name, func.line_number, func.class_name)
            if func_id not in seen:
                seen.add(func_id)
                result.append(func)

        # Limit to max calls
        return result[: self.max_llm_calls]

    def _has_test_smells(self, test_func: TestFunctionInfo) -> bool:
        """
        Check for obvious test smells that indicate problems.

        Args:
            test_func: Test function to check

        Returns:
            True if function has test smells
        """
        source_lower = test_func.source_code.lower()

        # Check for timing-related code (major smell)
        if "time.sleep" in source_lower or "asyncio.sleep" in source_lower:
            return True

        # Check for global state modification (major smell)
        if "global " in source_lower:
            return True

        # Check for hard-coded credentials (security smell)
        if any(
            keyword in source_lower
            for keyword in ["password =", "api_key =", "token =", "secret ="]
        ):
            # But exclude test fixtures and mocks
            if "mock" not in source_lower and "fixture" not in source_lower:
                return True

        # Check for database commits in tests (potential smell)
        if "commit()" in source_lower and "mock" not in source_lower:
            return True

        return False

    def _has_very_complex_assertions(self, test_func: TestFunctionInfo) -> bool:
        """
        Check if function has very complex assertions.

        More strict than before - only flags truly complex cases.

        Args:
            test_func: Test function to check

        Returns:
            True if function has very complex assertions
        """
        # Only flag if significantly complex
        if len(test_func.assertions) > self.min_assertions:
            return True

        # Check for complex assertion expressions
        complex_count = 0
        for assertion in test_func.assertions:
            if assertion.assertion_type == "other":
                complex_count += 1

        # Only flag if multiple complex assertions
        return complex_count >= 2

    def _find_similar_function_pairs(
        self, functions: List[TestFunctionInfo]
    ) -> List[tuple]:
        """
        Find pairs of very similar function names (potential merge candidates).

        Uses stricter similarity criteria than before.

        Args:
            functions: List of test functions

        Returns:
            List of (func1, func2) tuples
        """
        similar_pairs = []

        for i, func1 in enumerate(functions):
            for func2 in functions[i + 1 :]:
                # Only check within same class
                if func1.class_name != func2.class_name:
                    continue

                similarity = self._calculate_name_similarity(func1.name, func2.name)
                if similarity >= self.similarity_threshold:
                    similar_pairs.append((func1, func2))

        return similar_pairs

    def _calculate_name_similarity(self, name1: str, name2: str) -> float:
        """
        Calculate similarity score between two function names.

        Args:
            name1: First function name
            name2: Second function name

        Returns:
            Similarity score (0-1)
        """
        parts1 = set(name1.split("_"))
        parts2 = set(name2.split("_"))

        # Remove common test prefixes
        common_prefixes = {"test", "it", "should", "when", "given"}
        parts1 -= common_prefixes
        parts2 -= common_prefixes

        if not parts1 or not parts2:
            return 0.0

        # Jaccard similarity
        intersection = len(parts1 & parts2)
        union = len(parts1 | parts2)

        return intersection / union if union > 0 else 0.0

    def _has_unusual_decorator_patterns(self, test_func: TestFunctionInfo) -> bool:
        """
        Check if function has unusual decorator patterns.

        Args:
            test_func: Test function to check

        Returns:
            True if function has unusual patterns
        """
        # Check for many mock decorators (over-mocking smell)
        decorator_count = len(test_func.decorators)
        if decorator_count > self.min_decorators:
            return True

        # Check for mixing of async and sync decorators (potential issue)
        decorator_strs = [str(d) for d in test_func.decorators]
        has_async = any("async" in d.lower() for d in decorator_strs)
        has_sync_mock = any(
            "mock" in d.lower() or "patch" in d.lower() for d in decorator_strs
        )

        return has_async and has_sync_mock
