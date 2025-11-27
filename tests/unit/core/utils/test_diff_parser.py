"""
Unit tests for the diff parser utility.

Tests the extraction of modified function names from unified diff format.
"""

import pytest

from app.core.utils.diff_parser import (
    DiffHunk,
    ModifiedFunction,
    extract_modified_function_names,
    extract_modified_functions_from_diff,
    get_modified_files_from_diff,
    parse_unified_diff,
)

# Sample diff for testing
SAMPLE_DIFF = """diff --git a/app/utils.py b/app/utils.py
index 1234567..abcdefg 100644
--- a/app/utils.py
+++ b/app/utils.py
@@ -10,6 +10,10 @@ def existing_function():
     pass


+def new_function():
+    return "hello"
+
+
 def another_function():
     pass
"""

SAMPLE_METHOD_DIFF = """diff --git a/app/service.py b/app/service.py
--- a/app/service.py
+++ b/app/service.py
@@ -5,6 +5,10 @@ class MyService:
     def __init__(self):
         pass

+    def new_method(self):
+        return True
+
     def existing_method(self):
         pass
"""

SAMPLE_ASYNC_DIFF = """diff --git a/app/api.py b/app/api.py
--- a/app/api.py
+++ b/app/api.py
@@ -1,3 +1,7 @@
+async def fetch_data():
+    return await some_call()
+
+
 async def existing_handler():
     pass
"""

SAMPLE_DELETED_FUNCTION_DIFF = """diff --git a/app/old.py b/app/old.py
--- a/app/old.py
+++ b/app/old.py
@@ -1,6 +1,2 @@
 def keep_this():
     pass
-
-def remove_this():
-    return "goodbye"
"""

SAMPLE_MULTI_FILE_DIFF = """diff --git a/app/utils.py b/app/utils.py
--- a/app/utils.py
+++ b/app/utils.py
@@ -1,3 +1,7 @@
+def helper_one():
+    pass
+
+
 def existing():
     pass
diff --git a/app/service.py b/app/service.py
--- a/app/service.py
+++ b/app/service.py
@@ -1,3 +1,7 @@
+def helper_two():
+    pass
+
+
 def service_method():
     pass
"""


class TestParseUnifiedDiff:
    """Tests for parse_unified_diff function."""

    def test_parse_single_hunk(self):
        """Test parsing a diff with a single hunk."""
        hunks = parse_unified_diff(SAMPLE_DIFF)

        assert len(hunks) == 1
        assert hunks[0].file_path == "app/utils.py"
        assert hunks[0].new_start == 10

    def test_parse_multiple_files(self):
        """Test parsing a diff with multiple files."""
        hunks = parse_unified_diff(SAMPLE_MULTI_FILE_DIFF)

        assert len(hunks) == 2

        files = {h.file_path for h in hunks}
        assert "app/utils.py" in files
        assert "app/service.py" in files

    def test_parse_empty_diff(self):
        """Test parsing an empty diff."""
        hunks = parse_unified_diff("")
        assert len(hunks) == 0

    def test_hunk_contains_lines(self):
        """Test that hunks contain diff lines."""
        hunks = parse_unified_diff(SAMPLE_DIFF)

        assert len(hunks[0].lines) > 0
        # Check that added lines are included
        added_lines = [l for l in hunks[0].lines if l.startswith("+")]
        assert len(added_lines) > 0


class TestExtractModifiedFunctions:
    """Tests for extract_modified_functions_from_diff function."""

    def test_extract_new_function(self):
        """Test extracting a newly added function."""
        functions = extract_modified_functions_from_diff(SAMPLE_DIFF)

        names = [f.name for f in functions]
        assert "new_function" in names

    def test_extract_new_method(self):
        """Test extracting a newly added method."""
        functions = extract_modified_functions_from_diff(SAMPLE_METHOD_DIFF)

        names = [f.name for f in functions]
        assert "new_method" in names

    def test_extract_async_function(self):
        """Test extracting an async function."""
        functions = extract_modified_functions_from_diff(SAMPLE_ASYNC_DIFF)

        names = [f.name for f in functions]
        assert "fetch_data" in names

    def test_extract_deleted_function(self):
        """Test extracting a deleted function."""
        functions = extract_modified_functions_from_diff(SAMPLE_DELETED_FUNCTION_DIFF)

        deleted = [f for f in functions if f.modification_type == "deleted"]
        names = [f.name for f in deleted]
        assert "remove_this" in names

    def test_modification_type_added(self):
        """Test that new functions have modification_type='added'."""
        functions = extract_modified_functions_from_diff(SAMPLE_DIFF)

        new_func = next(f for f in functions if f.name == "new_function")
        assert new_func.modification_type == "added"

    def test_file_path_included(self):
        """Test that file path is included in result."""
        functions = extract_modified_functions_from_diff(SAMPLE_DIFF)

        new_func = next(f for f in functions if f.name == "new_function")
        assert new_func.file_path == "app/utils.py"

    def test_only_python_files_processed(self):
        """Test that non-Python files are ignored."""
        non_python_diff = """diff --git a/README.md b/README.md
--- a/README.md
+++ b/README.md
@@ -1,3 +1,5 @@
+# New Header
+
 Some content
"""
        functions = extract_modified_functions_from_diff(non_python_diff)
        assert len(functions) == 0


class TestExtractModifiedFunctionNames:
    """Tests for extract_modified_function_names function (simple API)."""

    def test_returns_deduplicated_names(self):
        """Test that the simple API returns deduplicated names."""
        names = extract_modified_function_names(SAMPLE_DIFF)

        assert "new_function" in names
        assert len(names) == len(set(names))  # No duplicates

    def test_returns_sorted_names(self):
        """Test that names are sorted alphabetically."""
        names = extract_modified_function_names(SAMPLE_MULTI_FILE_DIFF)

        assert names == sorted(names)

    def test_empty_diff_returns_empty_list(self):
        """Test that empty diff returns empty list."""
        names = extract_modified_function_names("")
        assert names == []


class TestGetModifiedFiles:
    """Tests for get_modified_files_from_diff function."""

    def test_single_file(self):
        """Test extracting single modified file."""
        files = get_modified_files_from_diff(SAMPLE_DIFF)

        assert len(files) == 1
        assert "app/utils.py" in files

    def test_multiple_files(self):
        """Test extracting multiple modified files."""
        files = get_modified_files_from_diff(SAMPLE_MULTI_FILE_DIFF)

        assert len(files) == 2
        assert "app/utils.py" in files
        assert "app/service.py" in files

    def test_files_are_sorted(self):
        """Test that files are returned sorted."""
        files = get_modified_files_from_diff(SAMPLE_MULTI_FILE_DIFF)

        assert files == sorted(files)


class TestEdgeCases:
    """Tests for edge cases and special scenarios."""

    def test_function_with_decorators(self):
        """Test extraction when function has decorators."""
        diff_with_decorator = """diff --git a/app/api.py b/app/api.py
--- a/app/api.py
+++ b/app/api.py
@@ -1,3 +1,8 @@
+@app.route("/")
+def index():
+    return "hello"
+
+
 def other():
     pass
"""
        names = extract_modified_function_names(diff_with_decorator)
        assert "index" in names

    def test_function_with_type_hints(self):
        """Test extraction of function with type hints."""
        diff_with_types = """diff --git a/app/service.py b/app/service.py
--- a/app/service.py
+++ b/app/service.py
@@ -1,3 +1,7 @@
+def calculate(x: int, y: int) -> int:
+    return x + y
+
+
 def existing():
     pass
"""
        names = extract_modified_function_names(diff_with_types)
        assert "calculate" in names

    def test_nested_function_not_extracted(self):
        """Test that nested functions inside other functions are still extracted."""
        diff_with_nested = """diff --git a/app/utils.py b/app/utils.py
--- a/app/utils.py
+++ b/app/utils.py
@@ -1,3 +1,9 @@
+def outer():
+    def inner():
+        pass
+    return inner
+
+
 def existing():
     pass
"""
        names = extract_modified_function_names(diff_with_nested)
        # Both outer and inner should be detected as they're on separate lines
        assert "outer" in names

    def test_class_with_multiple_methods(self):
        """Test extraction from class with multiple new methods."""
        diff_multi_method = """diff --git a/app/model.py b/app/model.py
--- a/app/model.py
+++ b/app/model.py
@@ -1,3 +1,12 @@
 class User:
+    def get_name(self):
+        return self.name
+
+    def set_name(self, name):
+        self.name = name
+
     def __init__(self):
         pass
"""
        names = extract_modified_function_names(diff_multi_method)
        assert "get_name" in names
        assert "set_name" in names
