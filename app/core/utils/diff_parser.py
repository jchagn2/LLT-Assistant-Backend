"""
Diff parser utility for extracting modified function names from git diffs.

This module provides utilities for parsing unified diff format and
extracting Python function names that were modified. Used by ImpactAnalyzer
to identify which functions need reverse dependency lookup.
"""

import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Set


@dataclass
class DiffHunk:
    """Represents a single hunk (change block) in a diff."""

    file_path: str
    old_start: int
    old_count: int
    new_start: int
    new_count: int
    lines: List[str]


@dataclass
class ModifiedFunction:
    """Represents a function that was modified in a diff."""

    name: str
    file_path: str
    line_number: int
    modification_type: str  # 'added', 'modified', 'deleted'


# Pattern to match Python function definitions
FUNCTION_PATTERN = re.compile(r"^(?:async\s+)?def\s+(\w+)\s*\(", re.MULTILINE)

# Pattern to match Python class definitions
CLASS_PATTERN = re.compile(r"^class\s+(\w+)\s*[:\(]", re.MULTILINE)

# Pattern to match method definitions (indented def)
METHOD_PATTERN = re.compile(r"^\s+(?:async\s+)?def\s+(\w+)\s*\(", re.MULTILINE)

# Pattern to match diff hunk header
HUNK_HEADER_PATTERN = re.compile(r"^@@\s+-(\d+)(?:,(\d+))?\s+\+(\d+)(?:,(\d+))?\s+@@")

# Pattern to match diff file header
FILE_HEADER_PATTERN = re.compile(
    r"^(?:diff --git a/|---|\+\+\+)\s*(?:a/|b/)?(.+?)(?:\s|$)"
)


def parse_unified_diff(diff_content: str) -> List[DiffHunk]:
    """
    Parse unified diff format into structured hunks.

    Args:
        diff_content: Raw unified diff string

    Returns:
        List of DiffHunk objects
    """
    hunks = []
    current_file = None
    current_hunk = None
    hunk_lines = []

    lines = diff_content.split("\n")
    i = 0

    while i < len(lines):
        line = lines[i]

        # Check for file header (diff --git, ---, +++)
        if line.startswith("diff --git"):
            # Extract file path from "diff --git a/path b/path"
            match = re.search(r"diff --git a/(.+?) b/(.+)", line)
            if match:
                current_file = match.group(2)

        elif line.startswith("+++"):
            # Use +++ line for more accurate file path
            match = re.search(r"\+\+\+ (?:b/)?(.+)", line)
            if match and match.group(1) != "/dev/null":
                current_file = match.group(1)

        elif line.startswith("@@"):
            # Save previous hunk if exists
            if current_hunk is not None:
                current_hunk.lines = hunk_lines
                hunks.append(current_hunk)
                hunk_lines = []

            # Parse hunk header
            match = HUNK_HEADER_PATTERN.match(line)
            if match and current_file:
                old_start = int(match.group(1))
                old_count = int(match.group(2)) if match.group(2) else 1
                new_start = int(match.group(3))
                new_count = int(match.group(4)) if match.group(4) else 1

                current_hunk = DiffHunk(
                    file_path=current_file,
                    old_start=old_start,
                    old_count=old_count,
                    new_start=new_start,
                    new_count=new_count,
                    lines=[],
                )

        elif current_hunk is not None:
            # Collect hunk content lines
            if not line.startswith("\\"):  # Skip "\ No newline at end of file"
                hunk_lines.append(line)

        i += 1

    # Save last hunk
    if current_hunk is not None:
        current_hunk.lines = hunk_lines
        hunks.append(current_hunk)

    return hunks


def extract_function_at_line(content: str, target_line: int) -> Optional[str]:
    """
    Find the function name that contains the given line number.

    Args:
        content: Full file content
        target_line: Line number (1-indexed)

    Returns:
        Function name if found, None otherwise
    """
    lines = content.split("\n")

    # Build a map of function/method start lines to names
    current_class = None
    function_ranges: List[tuple] = []  # (start_line, name, is_method)

    for i, line in enumerate(lines, start=1):
        # Check for class definition
        class_match = CLASS_PATTERN.match(line)
        if class_match:
            current_class = class_match.group(1)
            continue

        # Check for function definition (not indented)
        func_match = FUNCTION_PATTERN.match(line)
        if func_match:
            function_ranges.append((i, func_match.group(1), False))
            current_class = None  # Reset class context for module-level functions
            continue

        # Check for method definition (indented)
        method_match = METHOD_PATTERN.match(line)
        if method_match and current_class:
            # Store as ClassName.method_name
            method_name = f"{current_class}.{method_match.group(1)}"
            function_ranges.append((i, method_name, True))

    # Find which function contains the target line
    for i in range(len(function_ranges)):
        start_line, name, _ = function_ranges[i]

        # Determine end line (start of next function or end of file)
        if i + 1 < len(function_ranges):
            end_line = function_ranges[i + 1][0] - 1
        else:
            end_line = len(lines)

        if start_line <= target_line <= end_line:
            return name

    return None


def extract_modified_functions_from_diff(
    diff_content: str,
    file_contents: Optional[Dict[str, str]] = None,
) -> List[ModifiedFunction]:
    """
    Extract function names that were modified in a git diff.

    Args:
        diff_content: Raw unified diff string
        file_contents: Optional dict mapping file paths to their contents
                      (for context-aware extraction)

    Returns:
        List of ModifiedFunction objects
    """
    hunks = parse_unified_diff(diff_content)
    modified_functions: List[ModifiedFunction] = []
    seen_functions: Set[tuple] = set()  # (file_path, name) to avoid duplicates

    for hunk in hunks:
        # Only process Python files
        if not hunk.file_path.endswith(".py"):
            continue

        current_line = hunk.new_start

        for line in hunk.lines:
            if line.startswith("+") and not line.startswith("+++"):
                # This is an added line
                content = line[1:]  # Remove the '+' prefix

                # Check if this line is a function definition
                func_match = FUNCTION_PATTERN.match(content)
                method_match = METHOD_PATTERN.match(content)

                if func_match:
                    func_name = func_match.group(1)
                    key = (hunk.file_path, func_name)
                    if key not in seen_functions:
                        modified_functions.append(
                            ModifiedFunction(
                                name=func_name,
                                file_path=hunk.file_path,
                                line_number=current_line,
                                modification_type="added",
                            )
                        )
                        seen_functions.add(key)

                elif method_match:
                    method_name = method_match.group(1)
                    key = (hunk.file_path, method_name)
                    if key not in seen_functions:
                        modified_functions.append(
                            ModifiedFunction(
                                name=method_name,
                                file_path=hunk.file_path,
                                line_number=current_line,
                                modification_type="added",
                            )
                        )
                        seen_functions.add(key)

                current_line += 1

            elif line.startswith("-") and not line.startswith("---"):
                # This is a deleted line - check if it's a function being deleted
                content = line[1:]

                func_match = FUNCTION_PATTERN.match(content)
                method_match = METHOD_PATTERN.match(content)

                if func_match:
                    func_name = func_match.group(1)
                    key = (hunk.file_path, func_name)
                    if key not in seen_functions:
                        modified_functions.append(
                            ModifiedFunction(
                                name=func_name,
                                file_path=hunk.file_path,
                                line_number=current_line,
                                modification_type="deleted",
                            )
                        )
                        seen_functions.add(key)

                elif method_match:
                    method_name = method_match.group(1)
                    key = (hunk.file_path, method_name)
                    if key not in seen_functions:
                        modified_functions.append(
                            ModifiedFunction(
                                name=method_name,
                                file_path=hunk.file_path,
                                line_number=current_line,
                                modification_type="deleted",
                            )
                        )
                        seen_functions.add(key)

            else:
                # Context line (unchanged) - still increment line number
                if not line.startswith("-"):
                    current_line += 1

    return modified_functions


def extract_modified_function_names(diff_content: str) -> List[str]:
    """
    Simple API to extract just the function names from a diff.

    This is the primary API for impact analysis. Returns a deduplicated
    list of function names that were modified.

    Args:
        diff_content: Raw unified diff string

    Returns:
        List of function names (deduplicated)
    """
    modified = extract_modified_functions_from_diff(diff_content)
    names = list({func.name for func in modified})
    return sorted(names)


def get_modified_files_from_diff(diff_content: str) -> List[str]:
    """
    Extract list of modified file paths from a diff.

    Args:
        diff_content: Raw unified diff string

    Returns:
        List of file paths that were modified
    """
    hunks = parse_unified_diff(diff_content)
    files = list({hunk.file_path for hunk in hunks})
    return sorted(files)


def extract_and_classify_modified_functions(
    diff_content: str, use_ast: bool = True
) -> List["ClassifiedChange"]:
    """
    Extract and classify modified functions from git diff.

    This is an enhanced version of extract_modified_function_names()
    that includes change classification (functional vs non-functional).

    Args:
        diff_content: Raw unified diff string
        use_ast: Enable AST analysis (default: True for hybrid mode)

    Returns:
        List of ClassifiedChange objects with classification

    Example:
        >>> diff = "diff --git a/app.py b/app.py\\n..."
        >>> changes = extract_and_classify_modified_functions(diff)
        >>> for change in changes:
        ...     print(f"{change.function_name}: {change.change_type}")
    """
    from app.core.utils.change_classifier import ChangeClassifier

    classifier = ChangeClassifier(use_ast=use_ast)
    return classifier.classify_changes(diff_content)
