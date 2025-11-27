# from math_functions import greet
import pytest

from data.raw.simple.simple import greet


class TestGreet:
    """Test suite for the greet function"""

    def test_greet_basic_name(self):
        """Test greeting with a basic name"""
        result = greet("Alice")
        assert result == "Hello, Alice!"

    def test_greet_empty_string(self):
        """Test greeting with an empty string"""
        result = greet("")
        assert result == "Hello, !"

    def test_greet_with_spaces(self):
        """Test greeting with names containing spaces"""
        result = greet("John Doe")
        assert result == "Hello, John Doe!"

    def test_greet_special_characters(self):
        """Test greeting with special characters"""
        result = greet("User123!")
        assert result == "Hello, User123!!"

    def test_greet_unicode_characters(self):
        """Test greeting with unicode characters"""
        result = greet("张三")
        assert result == "Hello, 张三!"

    def test_greet_long_name(self):
        """Test greeting with a long name"""
        long_name = "A" * 1000
        result = greet(long_name)
        assert result == f"Hello, {long_name}!"

    def test_greet_numeric_string(self):
        """Test greeting with numeric strings"""
        result = greet("123")
        assert result == "Hello, 123!"

    def test_greet_with_punctuation(self):
        """Test greeting with punctuation in name"""
        result = greet("Dr. Smith, PhD")
        assert result == "Hello, Dr. Smith, PhD!"

    def test_greet_whitespace_only(self):
        """Test greeting with whitespace-only name"""
        result = greet("   ")
        assert result == "Hello,    !"

    def test_greet_newline_character(self):
        """Test greeting with newline character"""
        result = greet("Alice\nBob")
        assert result == "Hello, Alice\nBob!"

    def test_greet_return_type(self):
        """Test that the function returns a string"""
        result = greet("Test")
        assert isinstance(result, str)

    def test_greet_format_correctness(self):
        """Test that the greeting follows the expected format"""
        name = "TestUser"
        result = greet(name)
        assert result.startswith("Hello, ")
        assert result.endswith("!")
        assert name in result

    def test_greet_multiple_calls(self):
        """Test multiple consecutive calls"""
        names = ["Alice", "Bob", "Charlie"]
        expected_results = ["Hello, Alice!", "Hello, Bob!", "Hello, Charlie!"]

        for name, expected in zip(names, expected_results):
            result = greet(name)
            assert result == expected
