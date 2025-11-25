# from complex_functions import read_and_process_file
import os
import tempfile
from unittest.mock import mock_open, patch

import pytest

from data.raw.simple.simple2 import read_and_process_file


class TestReadAndProcessFile:
    """Test cases for read_and_process_file function"""

    def test_read_and_process_file_success(self):
        """Test successful file reading and processing"""
        # Create a temporary file with test content
        with tempfile.NamedTemporaryFile(mode="w", delete=False, encoding="utf-8") as f:
            f.write("hello\nworld\npython\ntesting")
            temp_file_path = f.name
        try:
            # Define a simple processor function
            def uppercase_processor(line):
                return line.upper()

            # Test the function
            result = read_and_process_file(temp_file_path, uppercase_processor)

            # Assertions
            expected = ["HELLO", "WORLD", "PYTHON", "TESTING"]
            assert result == expected
            assert len(result) == 4
            assert isinstance(result, list)

        finally:
            # Clean up
            os.unlink(temp_file_path)

    def test_read_and_process_file_empty_file(self):
        """Test processing an empty file"""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, encoding="utf-8") as f:
            f.write("")  # Empty file
            temp_file_path = f.name
        try:

            def identity_processor(line):
                return line

            result = read_and_process_file(temp_file_path, identity_processor)
            assert result == []
            assert len(result) == 0

        finally:
            os.unlink(temp_file_path)

    def test_read_and_process_file_with_whitespace(self):
        """Test file with leading/trailing whitespace and empty lines"""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, encoding="utf-8") as f:
            f.write("  hello  \n\nworld  \n  \npython\n")
            temp_file_path = f.name
        try:

            def strip_processor(line):
                return line.strip()

            result = read_and_process_file(temp_file_path, strip_processor)
            expected = ["hello", "", "world", "", "python", ""]
            assert result == expected

        finally:
            os.unlink(temp_file_path)

    def test_read_and_process_file_complex_processor(self):
        """Test with a more complex processor function"""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, encoding="utf-8") as f:
            f.write("123\n456\n789")
            temp_file_path = f.name
        try:

            def multiply_processor(line):
                try:
                    return str(int(line) * 2)
                except ValueError:
                    return "invalid"

            result = read_and_process_file(temp_file_path, multiply_processor)
            expected = ["246", "912", "1578"]
            assert result == expected

        finally:
            os.unlink(temp_file_path)

    def test_read_and_process_file_nonexistent_file(self):
        """Test handling of non-existent file"""
        non_existent_path = "/path/that/does/not/exist.txt"

        # Mock print to capture the warning message
        with patch("builtins.print") as mock_print:
            result = read_and_process_file(non_existent_path, lambda x: x)

            # Assertions
            assert result == []
            assert len(result) == 0
            mock_print.assert_called_once()
            call_args = mock_print.call_args[0][0]
            assert "not found" in call_args
            assert "Returning empty list" in call_args

    def test_read_and_process_file_processor_returns_none(self):
        """Test processor function that returns None"""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, encoding="utf-8") as f:
            f.write("test\nlines\nhere")
            temp_file_path = f.name
        try:

            def none_processor(line):
                return None

            result = read_and_process_file(temp_file_path, none_processor)
            expected = [None, None, None]
            assert result == expected
            assert all(item is None for item in result)

        finally:
            os.unlink(temp_file_path)

    def test_read_and_process_file_processor_raises_exception(self):
        """Test processor function that raises an exception"""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, encoding="utf-8") as f:
            f.write("valid\ninvalid\nvalid")
            temp_file_path = f.name
        try:

            def failing_processor(line):
                if line == "invalid":
                    raise ValueError("Invalid line detected")
                return line.upper()

            # Should not raise exception, processor errors should be handled by the processor itself
            result = read_and_process_file(temp_file_path, failing_processor)
            # The function should process lines until the failing one
            # Note: This depends on whether the processor handles its own exceptions

        finally:
            os.unlink(temp_file_path)

    def test_read_and_process_file_single_line(self):
        """Test file with single line"""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, encoding="utf-8") as f:
            f.write("single line")
            temp_file_path = f.name
        try:

            def reverse_processor(line):
                return line[::-1]

            result = read_and_process_file(temp_file_path, reverse_processor)
            expected = ["enil elgnis"]
            assert result == expected
            assert len(result) == 1

        finally:
            os.unlink(temp_file_path)

    def test_read_and_process_file_unicode_content(self):
        """Test file with unicode characters"""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, encoding="utf-8") as f:
            f.write("你好\n世界\nPython测试")
            temp_file_path = f.name
        try:

            def length_processor(line):
                return str(len(line))

            result = read_and_process_file(temp_file_path, length_processor)
            expected = ["2", "2", "7"]  # Lengths of the strings
            assert result == expected

        finally:
            os.unlink(temp_file_path)

    def test_read_and_process_file_large_file(self):
        """Test with a larger file to ensure proper line-by-line processing"""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, encoding="utf-8") as f:
            # Create 1000 lines
            for i in range(1000):
                f.write(f"line {i}\n")
            temp_file_path = f.name
        try:

            def counter_processor(line):
                return f"processed: {line}"

            result = read_and_process_file(temp_file_path, counter_processor)

            # Assertions
            assert len(result) == 1000
            assert all(line.startswith("processed: line") for line in result)
            assert result[0] == "processed: line 0"
            assert result[999] == "processed: line 999"

        finally:
            os.unlink(temp_file_path)

    def test_read_and_process_file_identity_processor(self):
        """Test with identity processor (returns input as-is)"""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, encoding="utf-8") as f:
            f.write("original\ncontent\npreserved")
            temp_file_path = f.name
        try:

            def identity_processor(line):
                return line

            result = read_and_process_file(temp_file_path, identity_processor)
            expected = ["original", "content", "preserved"]
            assert result == expected

        finally:
            os.unlink(temp_file_path)

    @patch("builtins.open", new_callable=mock_open, read_data="mocked\ncontent\nhere")
    def test_read_and_process_file_with_mock(self, mock_file):
        """Test using mock to simulate file reading"""

        def uppercase_processor(line):
            return line.upper()

        result = read_and_process_file("dummy_path.txt", uppercase_processor)

        expected = ["MOCKED", "CONTENT", "HERE"]
        assert result == expected
        mock_file.assert_called_once_with("dummy_path.txt", "r", encoding="utf-8")
