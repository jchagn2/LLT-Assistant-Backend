"""
Change classifier for distinguishing functional vs non-functional code changes.

This module provides hybrid classification (heuristics + AST) to determine
whether git diff changes are functional (logic modifications) or non-functional
(comments, docstrings, formatting, whitespace).
"""

import ast
import re
from dataclasses import dataclass
from typing import List, Literal, Optional

from app.core.utils.diff_parser import DiffHunk, parse_unified_diff


@dataclass
class ClassifiedChange:
    """Represents a classified code change from a git diff."""

    function_name: str
    file_path: str
    change_type: Literal["functional", "non-functional", "mixed"]
    confidence: float  # 0.0-1.0
    reasons: List[str]  # Why classified this way
    hunk_content: str  # Original diff hunk for reference


# Non-Functional Patterns (fast detection)
NON_FUNCTIONAL_PATTERNS = [
    # Comments
    r"^\s*#",  # Comment lines
    r"^\s*'''",  # Docstring start/end (single quotes)
    r'^\s*"""',  # Docstring start/end (double quotes)
    # Whitespace/Formatting
    r"^\s*$",  # Empty lines
    r"^[\s\t]+$",  # Whitespace-only lines
    # Imports (often non-functional for test impact)
    r"^import\s+",
    r"^from\s+.+\s+import\s+",
]

# Functional Patterns (fast detection)
FUNCTIONAL_PATTERNS = [
    r"^\s*return\s+",  # Return statements
    r"^\s*if\s+",  # Control flow
    r"^\s*elif\s+",
    r"^\s*else\s*:",
    r"^\s*for\s+",
    r"^\s*while\s+",
    r"^\s*raise\s+",  # Error handling
    r"^\s*assert\s+",  # Assertions
    r"^\s*\w+\s*=(?!=)",  # Assignments (not ==)
    r"\..*\(",  # Method calls
    r"^\s*def\s+",  # Function definitions
    r"^\s*class\s+",  # Class definitions
    r"^\s*try\s*:",  # Exception handling
    r"^\s*except\s+",
    r"^\s*finally\s*:",
    r"^\s*with\s+",  # Context managers
]


class ChangeClassifier:
    """Hybrid classifier for functional vs non-functional changes."""

    def __init__(self, use_ast: bool = True):
        """
        Initialize the change classifier.

        Args:
            use_ast: Enable AST analysis for ambiguous cases (default: True)
        """
        self.use_ast = use_ast

    def classify_changes(self, diff_content: str) -> List[ClassifiedChange]:
        """
        Classify changes in git diff as functional or non-functional.

        Uses hybrid approach:
        1. Heuristic filtering for obvious cases
        2. AST analysis for ambiguous cases (if enabled)

        Args:
            diff_content: Raw unified diff string

        Returns:
            List of ClassifiedChange objects with classification
        """
        if not diff_content or not diff_content.strip():
            return []

        hunks = parse_unified_diff(diff_content)
        if not hunks:
            return []

        classified_changes: List[ClassifiedChange] = []

        for hunk in hunks:
            # Only process Python files
            if not hunk.file_path.endswith(".py"):
                continue

            # Extract function names from the hunk
            function_names = self._extract_function_names_from_hunk(hunk)

            if not function_names:
                # No function detected, classify the hunk as a whole
                function_names = [f"<file-level-change>"]

            for func_name in function_names:
                # Try heuristic classification first
                heuristic_result = self._classify_hunk_heuristic(hunk)

                if heuristic_result is not None:
                    # Heuristic gave clear answer
                    change_type = heuristic_result
                    confidence = 0.9  # High confidence for clear patterns
                    reasons = self._get_heuristic_reasons(hunk, change_type)
                else:
                    # Ambiguous - use AST if enabled
                    if self.use_ast:
                        change_type = self._classify_hunk_ast(hunk)
                        confidence = 0.7  # Medium confidence for AST
                        reasons = ["AST semantic analysis detected logic changes"]
                    else:
                        # Default to functional for safety
                        change_type = "functional"
                        confidence = 0.5
                        reasons = ["Ambiguous change, defaulting to functional"]

                classified_changes.append(
                    ClassifiedChange(
                        function_name=func_name,
                        file_path=hunk.file_path,
                        change_type=change_type,
                        confidence=confidence,
                        reasons=reasons,
                        hunk_content="\n".join(hunk.lines[:10]),  # First 10 lines
                    )
                )

        return classified_changes

    def _extract_function_names_from_hunk(self, hunk: DiffHunk) -> List[str]:
        """Extract function names that are being modified in the hunk."""
        function_names = []

        for line in hunk.lines:
            if line.startswith("+") and not line.startswith("+++"):
                content = line[1:]  # Remove '+' prefix
                # Check for function definition
                func_match = re.match(r"^\s*(?:async\s+)?def\s+(\w+)\s*\(", content)
                if func_match:
                    function_names.append(func_match.group(1))

            elif line.startswith("-") and not line.startswith("---"):
                content = line[1:]  # Remove '-' prefix
                func_match = re.match(r"^\s*(?:async\s+)?def\s+(\w+)\s*\(", content)
                if func_match:
                    func_name = func_match.group(1)
                    if func_name not in function_names:
                        function_names.append(func_name)

        return list(set(function_names))  # Deduplicate

    def _classify_hunk_heuristic(self, hunk: DiffHunk) -> Optional[str]:
        """
        Quick heuristic classification based on pattern matching.

        Returns:
            "functional" | "non-functional" | None (ambiguous, needs AST)
        """
        added_lines = [
            l[1:] for l in hunk.lines if l.startswith("+") and not l.startswith("+++")
        ]
        removed_lines = [
            l[1:] for l in hunk.lines if l.startswith("-") and not l.startswith("---")
        ]

        all_changed_lines = added_lines + removed_lines

        if not all_changed_lines:
            return "non-functional"

        # Count matches for each pattern type
        non_functional_count = 0
        functional_count = 0
        unmatched_count = 0

        for line in all_changed_lines:
            line_stripped = line.strip()

            # Skip empty lines
            if not line_stripped:
                non_functional_count += 1
                continue

            # Check non-functional patterns
            is_non_functional = any(re.match(p, line) for p in NON_FUNCTIONAL_PATTERNS)
            # Check functional patterns
            is_functional = any(re.match(p, line) for p in FUNCTIONAL_PATTERNS)

            if is_non_functional and not is_functional:
                non_functional_count += 1
            elif is_functional and not is_non_functional:
                functional_count += 1
            else:
                # Either both matched or neither matched
                unmatched_count += 1

        # Decision logic
        total_lines = len(all_changed_lines)

        if total_lines == 0:
            return "non-functional"

        # If 80%+ lines are non-functional, classify as non-functional
        if non_functional_count / total_lines >= 0.8 and functional_count == 0:
            return "non-functional"

        # If 80%+ lines are functional, classify as functional
        if functional_count / total_lines >= 0.8 and non_functional_count == 0:
            return "functional"

        # If we have any functional changes mixed with non-functional, it's ambiguous
        if functional_count > 0 and non_functional_count > 0:
            return None  # Ambiguous - need AST

        # If mostly unmatched, ambiguous
        if unmatched_count / total_lines > 0.5:
            return None

        # Default: if unsure, return None for AST analysis
        return None

    def _classify_hunk_ast(self, hunk: DiffHunk) -> str:
        """
        Deep AST-based semantic analysis for ambiguous changes.

        Compares the AST of old and new versions to detect actual logic changes.

        Returns:
            "functional" | "non-functional" | "mixed"
        """
        # Reconstruct old and new code versions
        old_lines = []
        new_lines = []

        for line in hunk.lines:
            if line.startswith("-") and not line.startswith("---"):
                old_lines.append(line[1:])  # Remove '-' prefix
            elif line.startswith("+") and not line.startswith("+++"):
                new_lines.append(line[1:])  # Remove '+' prefix
            elif not line.startswith("@@"):
                # Context line (unchanged)
                old_lines.append(line[1:] if line.startswith(" ") else line)
                new_lines.append(line[1:] if line.startswith(" ") else line)

        old_code = "\n".join(old_lines)
        new_code = "\n".join(new_lines)

        try:
            # Parse both versions
            old_ast_tree = ast.parse(old_code)
            new_ast_tree = ast.parse(new_code)

            # Compare AST structures (simplified - compare dumps)
            old_ast_dump = ast.dump(old_ast_tree)
            new_ast_dump = ast.dump(new_ast_tree)

            if old_ast_dump == new_ast_dump:
                return "non-functional"  # ASTs are identical
            else:
                return "functional"  # ASTs differ - logic changed

        except SyntaxError:
            # If we can't parse, assume functional for safety
            return "functional"

    def _get_heuristic_reasons(self, hunk: DiffHunk, change_type: str) -> List[str]:
        """
        Generate human-readable reasons for heuristic classification.

        Args:
            hunk: The diff hunk being classified
            change_type: The classification result

        Returns:
            List of reason strings
        """
        reasons = []

        added_lines = [
            l[1:] for l in hunk.lines if l.startswith("+") and not l.startswith("+++")
        ]
        removed_lines = [
            l[1:] for l in hunk.lines if l.startswith("-") and not l.startswith("---")
        ]

        if change_type == "non-functional":
            # Check what types of non-functional changes
            has_comments = any(
                re.match(r"^\s*#", line) for line in added_lines + removed_lines
            )
            has_docstrings = any(
                re.match(r'^\s*"""', line) or re.match(r"^\s*'''", line)
                for line in added_lines + removed_lines
            )
            has_whitespace = any(
                re.match(r"^\s*$", line) for line in added_lines + removed_lines
            )
            has_imports = any(
                re.match(r"^import\s+", line) or re.match(r"^from\s+.+\s+import", line)
                for line in added_lines + removed_lines
            )

            if has_comments:
                reasons.append("Comment-only changes")
            if has_docstrings:
                reasons.append("Docstring updates")
            if has_whitespace:
                reasons.append("Whitespace/formatting changes")
            if has_imports:
                reasons.append("Import statement changes")

            if not reasons:
                reasons.append("Non-functional changes detected")

        elif change_type == "functional":
            # Check what types of functional changes
            has_logic = any(
                re.match(r"^\s*return\s+", line)
                or re.match(r"^\s*if\s+", line)
                or re.match(r"^\s*for\s+", line)
                for line in added_lines + removed_lines
            )
            has_assignments = any(
                re.match(r"^\s*\w+\s*=(?!=)", line)
                for line in added_lines + removed_lines
            )
            has_function_defs = any(
                re.match(r"^\s*def\s+", line) for line in added_lines + removed_lines
            )

            if has_logic:
                reasons.append("Control flow or logic changes")
            if has_assignments:
                reasons.append("Variable assignment changes")
            if has_function_defs:
                reasons.append("Function definition changes")

            if not reasons:
                reasons.append("Functional code changes detected")

        return reasons if reasons else [f"{change_type} changes detected"]
