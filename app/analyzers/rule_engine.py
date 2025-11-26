"""Rule engine for detecting test quality issues."""

import ast
from abc import ABC, abstractmethod
from typing import List, Set

from app.analyzers.ast_parser import AssertionInfo, ParsedTestFile, TestFunctionInfo
from app.api.v1.schemas import Issue, IssueSuggestion
from app.core.constants import (
    ACTION_ADD,
    ACTION_REMOVE,
    ACTION_REPLACE,
    DETECTED_BY_RULE_ENGINE,
    EXTERNAL_DEPENDENCY_PATTERNS,
    ISSUE_TYPE_MISSING_ASSERTION,
    ISSUE_TYPE_MISSING_MOCK,
    ISSUE_TYPE_REDUNDANT_ASSERTION,
    ISSUE_TYPE_TRIVIAL_ASSERTION,
    ISSUE_TYPE_UNUSED_FIXTURE,
    ISSUE_TYPE_UNUSED_VARIABLE,
    MOCK_INDICATOR_PATTERNS,
    Severity,
)


class Rule(ABC):
    """Base class for detection rules."""

    def __init__(self, rule_id: str, severity: str, message_template: str):
        self.rule_id = rule_id
        self.severity = severity
        self.message_template = message_template

    @abstractmethod
    def check(self, parsed_file: ParsedTestFile) -> List[Issue]:
        """Run the rule and return detected issues."""
        pass

    def create_issue(
        self,
        file_path: str,
        line: int,
        column: int = 0,
        message: str = "",
        suggestion: IssueSuggestion = None,
    ) -> Issue:
        """Create an issue with the rule's default properties."""
        return Issue(
            file=file_path,
            line=line,
            column=column,
            severity=self.severity,
            type=self.rule_id,
            message=message or self.message_template,
            detected_by=DETECTED_BY_RULE_ENGINE,
            suggestion=suggestion
            or IssueSuggestion(
                action=ACTION_REMOVE, explanation="No specific suggestion provided"
            ),
        )


class RedundantAssertionRule(Rule):
    """Detect duplicate assertions within the same test function."""

    def __init__(self):
        super().__init__(
            rule_id=ISSUE_TYPE_REDUNDANT_ASSERTION,
            severity=Severity.WARNING.value,
            message_template="Duplicate assertion found",
        )

    def check(self, parsed_file: ParsedTestFile) -> List[Issue]:
        """Check for redundant assertions in test functions."""
        issues = []

        # Check module-level test functions
        for test_func in parsed_file.test_functions:
            issues.extend(self._check_function(test_func, parsed_file.file_path))

        # Check test class methods
        for test_class in parsed_file.test_classes:
            for test_method in test_class.methods:
                issues.extend(self._check_function(test_method, parsed_file.file_path))

        return issues

    def _check_function(
        self, test_func: TestFunctionInfo, file_path: str
    ) -> List[Issue]:
        """Check a single test function for redundant assertions."""
        issues = []
        seen_assertions = {}

        for assertion in test_func.assertions:
            # Create a canonical representation of the assertion
            assertion_key = self._get_assertion_key(assertion)

            if assertion_key in seen_assertions:
                # Found a duplicate
                original = seen_assertions[assertion_key]
                suggestion = IssueSuggestion(
                    action=ACTION_REMOVE,
                    old_code=assertion.source_code,
                    new_code=None,
                    explanation=(
                        f"This assertion is identical to the one at line "
                        f"{original.line_number}. Remove to reduce redundancy."
                    ),
                )

                issues.append(
                    self.create_issue(
                        file_path=file_path,
                        line=assertion.line_number,
                        column=assertion.column,
                        message=f"Redundant assertion: same as line {original.line_number}",
                        suggestion=suggestion,
                    )
                )
            else:
                seen_assertions[assertion_key] = assertion

        return issues

    def _get_assertion_key(self, assertion: AssertionInfo) -> str:
        """Get a canonical key for comparing assertions."""
        # Remove comments and normalize whitespace for comparison
        # Split on '#' to remove inline comments
        code_without_comment = assertion.source_code.split("#")[0].strip()
        # Normalize whitespace
        normalized = " ".join(code_without_comment.split())
        return normalized


class MissingAssertionRule(Rule):
    """Detect test functions with no assertions."""

    def __init__(self):
        super().__init__(
            rule_id=ISSUE_TYPE_MISSING_ASSERTION,
            severity=Severity.ERROR.value,
            message_template="Test function has no assertions",
        )

    def check(self, parsed_file: ParsedTestFile) -> List[Issue]:
        """Check for test functions without assertions."""
        issues = []

        # Check module-level test functions
        for test_func in parsed_file.test_functions:
            if self._has_no_assertions(test_func):
                issues.append(
                    self._create_missing_assertion_issue(
                        test_func, parsed_file.file_path
                    )
                )

        # Check test class methods
        for test_class in parsed_file.test_classes:
            for test_method in test_class.methods:
                if self._has_no_assertions(test_method):
                    issues.append(
                        self._create_missing_assertion_issue(
                            test_method, parsed_file.file_path
                        )
                    )

        return issues

    def _has_no_assertions(self, test_func: TestFunctionInfo) -> bool:
        """Check if test function has no assertions."""
        # Check for assertions
        if test_func.assertions:
            return False

        # Check for pytest.raises usage (exception testing)
        # This is a simplified check - could be enhanced with AST analysis
        if "pytest.raises" in test_func.source_code:
            return False

        return True

    def _create_missing_assertion_issue(
        self, test_func: TestFunctionInfo, file_path: str
    ) -> Issue:
        """Create an issue for missing assertions."""
        suggestion = IssueSuggestion(
            action=ACTION_ADD,
            old_code=None,
            new_code="    assert result is not None  # Add appropriate assertion",
            explanation="Add assertions to verify the expected behavior of your test.",
        )

        return self.create_issue(
            file_path=file_path,
            line=test_func.line_number,
            message=f"Test function '{test_func.name}' has no assertions",
            suggestion=suggestion,
        )


class TrivialAssertionRule(Rule):
    """Detect trivial assertions that always pass."""

    def __init__(self):
        super().__init__(
            rule_id=ISSUE_TYPE_TRIVIAL_ASSERTION,
            severity=Severity.ERROR.value,
            message_template="Trivial assertion that always passes",
        )

    def check(self, parsed_file: ParsedTestFile) -> List[Issue]:
        """Check for trivial assertions."""
        issues = []

        # Check module-level test functions
        for test_func in parsed_file.test_functions:
            issues.extend(self._check_function(test_func, parsed_file.file_path))

        # Check test class methods
        for test_class in parsed_file.test_classes:
            for test_method in test_class.methods:
                issues.extend(self._check_function(test_method, parsed_file.file_path))

        return issues

    def _check_function(
        self, test_func: TestFunctionInfo, file_path: str
    ) -> List[Issue]:
        """Check a single test function for trivial assertions."""
        issues = []

        for assertion in test_func.assertions:
            if assertion.is_trivial:
                suggestion = IssueSuggestion(
                    action=ACTION_REPLACE,
                    old_code=assertion.source_code,
                    new_code="    assert actual_result == expected_result",
                    explanation="Replace with a meaningful assertion that tests actual behavior.",
                )

                issues.append(
                    self.create_issue(
                        file_path=file_path,
                        line=assertion.line_number,
                        column=assertion.column,
                        message=f"Trivial assertion: {assertion.source_code.strip()}",
                        suggestion=suggestion,
                    )
                )

        return issues


class UnusedFixtureRule(Rule):
    """Detect fixtures that are defined but never used."""

    def __init__(self):
        super().__init__(
            rule_id=ISSUE_TYPE_UNUSED_FIXTURE,
            severity=Severity.INFO.value,
            message_template="Fixture is defined but never used",
        )

    def check(self, parsed_file: ParsedTestFile) -> List[Issue]:
        """Check for unused fixtures."""
        issues = []

        # Build set of used fixtures
        used_fixtures = self._get_used_fixtures(parsed_file)

        # Check each fixture
        for fixture in parsed_file.fixtures:
            if fixture.name not in used_fixtures:
                suggestion = IssueSuggestion(
                    action=ACTION_REMOVE,
                    old_code=(
                        f"@pytest.fixture\ndef {fixture.name}():\n"
                        f"    # fixture implementation"
                    ),
                    new_code=None,
                    explanation="Remove unused fixture to reduce code complexity.",
                )

                issues.append(
                    self.create_issue(
                        file_path=parsed_file.file_path,
                        line=fixture.line_number,
                        message=f"Fixture '{fixture.name}' is defined but never used",
                        suggestion=suggestion,
                    )
                )

        return issues

    def _get_used_fixtures(self, parsed_file: ParsedTestFile) -> Set[str]:
        """Get set of fixture names that are used in test functions."""
        used_fixtures = set()

        # Check module-level test functions
        for test_func in parsed_file.test_functions:
            used_fixtures.update(test_func.parameters)

        # Check test class methods
        for test_class in parsed_file.test_classes:
            for test_method in test_class.methods:
                used_fixtures.update(test_method.parameters)

        return used_fixtures


class UnusedVariableRule(Rule):
    """Detect variables that are defined but never used."""

    def __init__(self):
        super().__init__(
            rule_id=ISSUE_TYPE_UNUSED_VARIABLE,
            severity=Severity.INFO.value,
            message_template="Variable is defined but never used",
        )

    def check(self, parsed_file: ParsedTestFile) -> List[Issue]:
        """Check for unused variables in test functions."""
        issues = []

        # Check module-level test functions
        for test_func in parsed_file.test_functions:
            issues.extend(
                self._check_function_variables(test_func, parsed_file.file_path)
            )

        # Check test class methods
        for test_class in parsed_file.test_classes:
            for test_method in test_class.methods:
                issues.extend(
                    self._check_function_variables(test_method, parsed_file.file_path)
                )

        return issues

    def _check_function_variables(
        self, test_func: TestFunctionInfo, file_path: str
    ) -> List[Issue]:
        """Check for unused variables in a test function."""
        issues = []

        try:
            # Parse the function body
            func_ast = ast.parse(test_func.source_code)
            if not func_ast.body or not isinstance(
                func_ast.body[0], (ast.FunctionDef, ast.AsyncFunctionDef)
            ):
                return issues

            func_node = func_ast.body[0]

            # Find all variable assignments and references
            assigned_vars = set()
            referenced_vars = set()

            for node in ast.walk(func_node):
                # Variable assignments
                if isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name) and target.id != "_":
                            assigned_vars.add(target.id)
                        elif isinstance(target, ast.Tuple):
                            for elt in target.elts:
                                if isinstance(elt, ast.Name) and elt.id != "_":
                                    assigned_vars.add(elt.id)

                # Variable references
                elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
                    referenced_vars.add(node.id)

            # Find unused variables (exclude function parameters)
            unused_vars = assigned_vars - referenced_vars - set(test_func.parameters)

            # Create issues for unused variables
            for var_name in unused_vars:
                # Find the line where the variable is assigned
                line_number = self._find_assignment_line(func_node, var_name)

                suggestion = IssueSuggestion(
                    action=ACTION_REMOVE,
                    old_code=f"    {var_name} = ",  # Simplified - could be more specific
                    new_code=None,
                    explanation=f"Remove unused variable '{var_name}' to reduce code complexity.",
                )

                issues.append(
                    self.create_issue(
                        file_path=file_path,
                        line=test_func.line_number + line_number - 1,
                        message=f"Unused variable '{var_name}' is assigned but never used",
                        suggestion=suggestion,
                    )
                )

        except SyntaxError:
            # Skip functions with syntax errors
            pass

        return issues

    def _find_assignment_line(self, func_node: ast.FunctionDef, var_name: str) -> int:
        """Find the line number where a variable is assigned."""
        for node in ast.walk(func_node):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == var_name:
                        return node.lineno
                    elif isinstance(target, ast.Tuple):
                        for elt in target.elts:
                            if isinstance(elt, ast.Name) and elt.id == var_name:
                                return node.lineno
        return 1  # Default to first line if not found


class MissingMockRule(Rule):
    """Detect test functions calling external dependencies without proper mocking.

    This rule uses graph-based dependency analysis to find functions that call
    external services (database, API, file I/O) without proper mock setup.
    """

    def __init__(self):
        super().__init__(
            rule_id=ISSUE_TYPE_MISSING_MOCK,
            severity=Severity.WARNING.value,
            message_template="Test calls external dependency without mocking",
        )
        # Graph dependency data will be injected before analysis
        self._dependency_data: dict = {}

    def set_dependency_data(self, data: dict) -> None:
        """Set graph-based dependency data for test functions.

        Args:
            data: Dictionary mapping test function names to their dependencies
                  Example: {"test_save_user": ["save_to_db", "send_email"]}
        """
        self._dependency_data = data

    def check(self, parsed_file: ParsedTestFile) -> List[Issue]:
        """Check for missing mocks in test functions."""
        issues = []

        # Check module-level test functions
        for test_func in parsed_file.test_functions:
            issues.extend(self._check_function(test_func, parsed_file))

        # Check test class methods
        for test_class in parsed_file.test_classes:
            for test_method in test_class.methods:
                issues.extend(self._check_function(test_method, parsed_file))

        return issues

    def _check_function(
        self, test_func: TestFunctionInfo, parsed_file: ParsedTestFile
    ) -> List[Issue]:
        """Check a single test function for missing mocks."""
        issues = []

        # Check if test has mock indicators
        has_mocking = self._has_mock_indicators(test_func, parsed_file)

        # Get dependencies - prefer graph data, fallback to AST analysis
        dependencies = self._get_dependencies(test_func)

        # Find external dependencies that may need mocking
        external_deps = self._find_external_dependencies(dependencies)

        if external_deps and not has_mocking:
            suggestion = IssueSuggestion(
                action=ACTION_ADD,
                old_code=None,
                new_code=self._generate_mock_suggestion(external_deps),
                explanation=(
                    f"Add mocks for external dependencies: {', '.join(external_deps)}. "
                    "This ensures tests are isolated and deterministic."
                ),
            )

            issues.append(
                self.create_issue(
                    file_path=parsed_file.file_path,
                    line=test_func.line_number,
                    message=(
                        f"Test '{test_func.name}' calls external dependencies "
                        f"({', '.join(external_deps)}) without proper mocking"
                    ),
                    suggestion=suggestion,
                )
            )

        return issues

    def _has_mock_indicators(
        self, test_func: TestFunctionInfo, parsed_file: ParsedTestFile
    ) -> bool:
        """Check if test function has mock-related setup.

        Looks for:
        - @patch decorators
        - Mock-related fixture parameters
        - Mock imports in the file
        - Mock usage in source code
        """
        # Check decorators
        for decorator in test_func.decorators:
            for pattern in MOCK_INDICATOR_PATTERNS:
                if pattern.lower() in decorator.lower():
                    return True

        # Check parameters (fixture injection)
        for param in test_func.parameters:
            for pattern in MOCK_INDICATOR_PATTERNS:
                if pattern.lower() in param.lower():
                    return True

        # Check source code for mock usage
        source_lower = test_func.source_code.lower()
        for pattern in MOCK_INDICATOR_PATTERNS:
            if pattern.lower() in source_lower:
                return True

        # Check file imports (ImportInfo objects have module and name fields)
        for imp in parsed_file.imports:
            for pattern in MOCK_INDICATOR_PATTERNS:
                # Check both module and name fields for mock indicators
                # Example: from unittest.mock import Mock -> module="unittest.mock", name="Mock"
                if (
                    pattern.lower() in imp.module.lower()
                    or pattern.lower() in imp.name.lower()
                ):
                    return True

        return False

    def _get_dependencies(self, test_func: TestFunctionInfo) -> List[str]:
        """Get dependencies for a test function.

        Uses graph data if available, otherwise falls back to AST analysis.
        """
        # Try graph data first
        if test_func.name in self._dependency_data:
            return self._dependency_data[test_func.name]

        # Fallback: Extract function calls from AST
        return self._extract_function_calls_from_ast(test_func)

    def _extract_function_calls_from_ast(
        self, test_func: TestFunctionInfo
    ) -> List[str]:
        """Extract function calls from test function source code using AST."""
        calls = []

        try:
            func_ast = ast.parse(test_func.source_code)

            for node in ast.walk(func_ast):
                if isinstance(node, ast.Call):
                    # Get the function name
                    if isinstance(node.func, ast.Name):
                        calls.append(node.func.id)
                    elif isinstance(node.func, ast.Attribute):
                        calls.append(node.func.attr)

        except SyntaxError:
            pass

        return list(set(calls))

    def _find_external_dependencies(self, dependencies: List[str]) -> List[str]:
        """Filter dependencies to find external ones that likely need mocking."""
        external = []

        for dep in dependencies:
            dep_lower = dep.lower()
            for pattern in EXTERNAL_DEPENDENCY_PATTERNS:
                if (
                    dep_lower.startswith(pattern.lower())
                    or pattern.lower() in dep_lower
                ):
                    external.append(dep)
                    break

        return external

    def _generate_mock_suggestion(self, external_deps: List[str]) -> str:
        """Generate mock setup suggestion code."""
        if not external_deps:
            return ""

        # Generate @patch decorators for each dependency
        patches = []
        for dep in external_deps[:3]:  # Limit to first 3
            patches.append(f'@patch("module.{dep}")')

        patch_code = "\n".join(patches)
        return (
            f"{patch_code}\n"
            f"def test_with_mocks(self, {'mock_' + ', mock_'.join(external_deps[:3])}):\n"
            f"    # Configure mock return values\n"
            f"    # mock_{external_deps[0]}.return_value = expected_value"
        )


class RuleEngine:
    """Orchestrates all detection rules."""

    def __init__(self):
        self._missing_mock_rule = MissingMockRule()
        self.rules = [
            RedundantAssertionRule(),
            MissingAssertionRule(),
            TrivialAssertionRule(),
            UnusedFixtureRule(),
            UnusedVariableRule(),
            self._missing_mock_rule,
        ]

    def set_graph_dependency_data(self, data: dict) -> None:
        """Set graph-based dependency data for mock detection.

        Args:
            data: Dictionary mapping test function names to their dependencies
                  Example: {"test_save_user": ["save_to_db", "send_email"]}
        """
        self._missing_mock_rule.set_dependency_data(data)

    def analyze(self, parsed_file: ParsedTestFile) -> List[Issue]:
        """Run all rules and aggregate issues."""
        issues = []
        for rule in self.rules:
            issues.extend(rule.check(parsed_file))
        return issues
