# from math_functions import reverse_string
import pytest

from data.raw.simple.simple import reverse_string


class TestReverseString:
    """Test cases for the reverse_string function."""

    def test_reverse_typical_string(self):
        """Test reversing a typical string with multiple characters."""
        result = reverse_string("hello")
        assert result == "olleh"

    def test_reverse_single_character(self):
        """Test reversing a single character string."""
        result = reverse_string("a")
        assert result == "a"

    def test_reverse_empty_string(self):
        """Test reversing an empty string."""
        result = reverse_string("")
        assert result == ""

    def test_reverse_string_with_spaces(self):
        """Test reversing a string containing spaces."""
        result = reverse_string("hello world")
        assert result == "dlrow olleh"

    def test_reverse_string_with_special_characters(self):
        """Test reversing a string with special characters."""
        result = reverse_string("!@#$%")
        assert result == "%$#@!"

    def test_reverse_string_with_numbers(self):
        """Test reversing a string containing numbers."""
        result = reverse_string("12345")
        assert result == "54321"

    def test_reverse_string_with_mixed_characters(self):
        """Test reversing a string with mixed character types."""
        result = reverse_string("a1!b2@c3#")
        assert result == "#3c@2b!1a"

    def test_reverse_palindrome_string(self):
        """Test reversing a palindrome string."""
        result = reverse_string("racecar")
        assert result == "racecar"

    def test_reverse_unicode_characters(self):
        """Test reversing a string with Unicode characters."""
        result = reverse_string("こんにちは")
        assert result == "はちにんこ"

    def test_reverse_string_with_whitespace(self):
        """Test reversing a string with various whitespace characters."""
        result = reverse_string("hello\tworld\n")
        assert result == "\ndlrow\tolleh"

    def test_reverse_long_string(self):
        """Test reversing a long string."""
        long_string = "a" * 1000
        result = reverse_string(long_string)
        assert result == long_string[::-1]

    def test_reverse_string_immutability(self):
        """Test that the original string is not modified."""
        original = "hello"
        result = reverse_string(original)
        assert original == "hello"  # Original should remain unchanged
        assert result == "olleh"  # Result should be reversed

    def test_reverse_string_identity(self):
        """Test that reversing an empty string returns the same object."""
        empty_string = ""
        result = reverse_string(empty_string)
        assert result is empty_string  # Empty strings are often interned

    def test_reverse_string_with_capital_letters(self):
        """Test reversing a string with capital letters."""
        result = reverse_string("Hello World")
        assert result == "dlroW olleH"

    def test_reverse_string_with_newlines(self):
        """Test reversing a string containing newlines."""
        result = reverse_string("hello\nworld")
        assert result == "dlrow\nolleh"

    def test_reverse_string_type_preservation(self):
        """Test that the return type is always a string."""
        test_cases = ["hello", "", "123", "!@#"]
        for test_case in test_cases:
            result = reverse_string(test_case)
            assert isinstance(result, str)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
