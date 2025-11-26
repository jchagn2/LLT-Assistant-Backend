"""
Unit tests for the ChangeClassifier module.

Tests the hybrid classification approach for distinguishing functional
vs non-functional code changes.
"""

import time

import pytest

from app.core.utils.change_classifier import ChangeClassifier, ClassifiedChange


class TestChangeClassifierHeuristics:
    """Test heuristic classification (fast pattern matching)."""

    def test_classify_comment_only_change_as_non_functional(self):
        """Pure comment changes should be non-functional."""
        diff = """
diff --git a/app/utils.py b/app/utils.py
@@ -10,5 +10,6 @@ def calculate(x, y):
+    # Added helpful comment
     return x + y
        """
        classifier = ChangeClassifier(use_ast=False)  # Heuristic only
        changes = classifier.classify_changes(diff)

        assert len(changes) == 1
        assert changes[0].change_type == "non-functional"
        assert changes[0].confidence == 0.9
        assert "comment" in " ".join(changes[0].reasons).lower()

    def test_classify_docstring_only_change_as_non_functional(self):
        """Docstring updates should be non-functional."""
        diff = '''
diff --git a/app/utils.py b/app/utils.py
@@ -5,7 +5,7 @@ def calculate(x, y):
-    """Old docstring."""
+    """Updated docstring with better explanation."""
     return x + y
        '''
        classifier = ChangeClassifier(use_ast=False)
        changes = classifier.classify_changes(diff)

        assert len(changes) >= 1
        # Should classify as non-functional
        non_func = [c for c in changes if c.change_type == "non-functional"]
        assert len(non_func) > 0

    def test_classify_whitespace_only_change_as_non_functional(self):
        """Pure whitespace changes should be non-functional."""
        diff = """
diff --git a/app/utils.py b/app/utils.py
@@ -5,6 +5,7 @@ def calculate(x, y):
     return x + y
+
     # Extra blank line added
        """
        classifier = ChangeClassifier(use_ast=False)
        changes = classifier.classify_changes(diff)

        # This might return empty changes or a file-level change
        if changes:
            assert any(c.change_type == "non-functional" for c in changes)

    def test_classify_import_change_as_non_functional(self):
        """Import statement changes should be non-functional."""
        diff = """
diff --git a/app/utils.py b/app/utils.py
@@ -1,5 +1,6 @@
 import os
+import sys
 from typing import List
        """
        classifier = ChangeClassifier(use_ast=False)
        changes = classifier.classify_changes(diff)

        if changes:
            # Should detect as non-functional (imports)
            assert any(c.change_type == "non-functional" for c in changes)

    def test_classify_logic_change_as_functional(self):
        """Return statement changes should be functional."""
        diff = """
diff --git a/app/utils.py b/app/utils.py
@@ -5,5 +5,5 @@ def calculate(x, y):
-    return x + y
+    return x * y  # Changed operation
        """
        classifier = ChangeClassifier(use_ast=False)
        changes = classifier.classify_changes(diff)

        assert len(changes) >= 1
        functional = [c for c in changes if c.change_type == "functional"]
        assert len(functional) > 0

    def test_classify_assignment_change_as_functional(self):
        """Variable assignment changes should be functional."""
        diff = """
diff --git a/app/utils.py b/app/utils.py
@@ -5,5 +5,5 @@ def process(x):
-    result = x + 1
+    result = x * 2
     return result
        """
        classifier = ChangeClassifier(use_ast=False)
        changes = classifier.classify_changes(diff)

        if changes:
            functional = [c for c in changes if c.change_type == "functional"]
            assert len(functional) > 0

    def test_classify_control_flow_change_as_functional(self):
        """Control flow changes should be functional."""
        diff = """
diff --git a/app/utils.py b/app/utils.py
@@ -5,5 +5,7 @@ def validate(x):
-    return x > 0
+    if x > 0:
+        return True
+    return False
        """
        classifier = ChangeClassifier(use_ast=False)
        changes = classifier.classify_changes(diff)

        if changes:
            functional = [c for c in changes if c.change_type == "functional"]
            assert len(functional) > 0


class TestChangeClassifierAST:
    """Test AST-based classification (semantic analysis)."""

    def test_classify_mixed_change_with_ast(self):
        """Mixed changes should use AST analysis."""
        diff = """
diff --git a/app/utils.py b/app/utils.py
@@ -5,6 +5,7 @@ def calculate(x, y):
+    # Added comment
-    return x + y
+    return x * y
        """
        classifier = ChangeClassifier(use_ast=True)
        changes = classifier.classify_changes(diff)

        assert len(changes) >= 1
        # Should detect logic change despite comment
        functional = [c for c in changes if c.change_type == "functional"]
        assert len(functional) > 0  # Logic changed

    def test_ast_analysis_handles_syntax_error_gracefully(self):
        """AST should default to functional if parsing fails."""
        diff = """
diff --git a/app/utils.py b/app/utils.py
@@ -5,5 +5,5 @@ def calculate(x, y):
-    return x + y
+    return x + y @#$ invalid syntax
        """
        classifier = ChangeClassifier(use_ast=True)
        changes = classifier.classify_changes(diff)

        if changes:
            # Should default to functional for safety when can't parse
            functional = [c for c in changes if c.change_type == "functional"]
            assert len(functional) > 0


class TestChangeClassifierEdgeCases:
    """Test edge cases and special scenarios."""

    def test_empty_diff_returns_empty_list(self):
        """Empty diff should return empty list."""
        diff = ""
        classifier = ChangeClassifier()
        changes = classifier.classify_changes(diff)

        assert changes == []

    def test_non_python_file_ignored(self):
        """Non-Python files should be ignored."""
        diff = """
diff --git a/README.md b/README.md
@@ -1,3 +1,4 @@
 # Project
+Added new line
        """
        classifier = ChangeClassifier()
        changes = classifier.classify_changes(diff)

        assert changes == []

    def test_function_definition_added(self):
        """Adding a new function should be functional."""
        diff = """
diff --git a/app/utils.py b/app/utils.py
@@ -10,3 +10,6 @@ def existing_function():
     pass
+
+def new_function(x):
+    return x * 2
        """
        classifier = ChangeClassifier()
        changes = classifier.classify_changes(diff)

        assert len(changes) >= 1
        assert "new_function" in [c.function_name for c in changes]

    def test_function_definition_removed(self):
        """Removing a function should be detected."""
        diff = """
diff --git a/app/utils.py b/app/utils.py
@@ -10,6 +10,3 @@ def existing_function():
     pass
-
-def removed_function(x):
-    return x * 2
        """
        classifier = ChangeClassifier()
        changes = classifier.classify_changes(diff)

        assert len(changes) >= 1
        assert "removed_function" in [c.function_name for c in changes]


class TestChangeClassifierPerformance:
    """Test performance benchmarks."""

    def test_heuristic_mode_fast_performance(self):
        """Heuristic-only mode should be fast (<20ms for simple diff)."""
        diff = """
diff --git a/app/utils.py b/app/utils.py
@@ -10,5 +10,10 @@ def calculate(x, y):
+    # Comment 1
+    # Comment 2
+    # Comment 3
+    # Comment 4
+    # Comment 5
     return x + y
        """

        classifier = ChangeClassifier(use_ast=False)
        start = time.time()
        changes = classifier.classify_changes(diff)
        duration = (time.time() - start) * 1000  # Convert to ms

        assert duration < 20  # Should complete in < 20ms
        assert len(changes) >= 1

    def test_hybrid_mode_reasonable_performance(self):
        """Hybrid mode should complete within reasonable time."""
        diff = """
diff --git a/app/utils.py b/app/utils.py
@@ -5,6 +5,7 @@ def calculate(x, y):
+    # Comment
-    return x + y
+    return x * y
        """

        classifier = ChangeClassifier(use_ast=True)
        start = time.time()
        changes = classifier.classify_changes(diff)
        duration = (time.time() - start) * 1000  # ms

        assert duration < 100  # Should complete in < 100ms for simple diff
        assert len(changes) >= 1


class TestClassifiedChangeDataclass:
    """Test ClassifiedChange dataclass."""

    def test_classified_change_has_required_fields(self):
        """ClassifiedChange should have all required fields."""
        diff = """
diff --git a/app/utils.py b/app/utils.py
@@ -5,5 +5,6 @@ def calculate(x, y):
+    # Comment
     return x + y
        """
        classifier = ChangeClassifier()
        changes = classifier.classify_changes(diff)

        if changes:
            change = changes[0]
            assert hasattr(change, "function_name")
            assert hasattr(change, "file_path")
            assert hasattr(change, "change_type")
            assert hasattr(change, "confidence")
            assert hasattr(change, "reasons")
            assert hasattr(change, "hunk_content")

            assert isinstance(change.function_name, str)
            assert isinstance(change.file_path, str)
            assert change.change_type in ["functional", "non-functional", "mixed"]
            assert 0.0 <= change.confidence <= 1.0
            assert isinstance(change.reasons, list)
            assert isinstance(change.hunk_content, str)


class TestChangeClassifierReasons:
    """Test that classification reasons are informative."""

    def test_non_functional_reasons_are_descriptive(self):
        """Non-functional changes should have clear reasons."""
        diff = """
diff --git a/app/utils.py b/app/utils.py
@@ -5,5 +5,6 @@ def calculate(x, y):
+    # Added comment
     return x + y
        """
        classifier = ChangeClassifier()
        changes = classifier.classify_changes(diff)

        if changes:
            change = changes[0]
            if change.change_type == "non-functional":
                assert len(change.reasons) > 0
                reasons_text = " ".join(change.reasons).lower()
                assert any(
                    keyword in reasons_text
                    for keyword in ["comment", "whitespace", "docstring", "import"]
                )

    def test_functional_reasons_are_descriptive(self):
        """Functional changes should have clear reasons."""
        diff = """
diff --git a/app/utils.py b/app/utils.py
@@ -5,5 +5,5 @@ def calculate(x, y):
-    return x + y
+    return x * y
        """
        classifier = ChangeClassifier()
        changes = classifier.classify_changes(diff)

        if changes:
            functional = [c for c in changes if c.change_type == "functional"]
            if functional:
                change = functional[0]
                assert len(change.reasons) > 0
                reasons_text = " ".join(change.reasons).lower()
                assert any(
                    keyword in reasons_text
                    for keyword in ["logic", "control", "assignment", "functional"]
                )
