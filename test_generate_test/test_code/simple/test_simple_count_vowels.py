# from math_functions import count_vowels
import pytest

from data.raw.simple.simple import count_vowels


class TestCountVowels:
    """Test cases for count_vowels function"""

    def test_count_vowels_empty_string(self):
        """Test counting vowels in an empty string"""
        result = count_vowels("")
        assert result == 0

    def test_count_vowels_no_vowels(self):
        """Test counting vowels in a string with no vowels"""
        result = count_vowels("bcdfghjklmnpqrstvwxyz")
        assert result == 0

    def test_count_vowels_all_vowels_lowercase(self):
        """Test counting all lowercase vowels"""
        result = count_vowels("aeiou")
        assert result == 5

    def test_count_vowels_all_vowels_uppercase(self):
        """Test counting all uppercase vowels"""
        result = count_vowels("AEIOU")
        assert result == 5

    def test_count_vowels_mixed_case(self):
        """Test counting vowels with mixed case"""
        result = count_vowels("aEiOu")
        assert result == 5

    def test_count_vowels_with_consonants(self):
        """Test counting vowels in a string with consonants"""
        result = count_vowels("hello world")
        assert result == 3  # e, o, o

    def test_count_vowels_with_numbers(self):
        """Test counting vowels in a string with numbers"""
        result = count_vowels("a1e2i3o4u5")
        assert result == 5

    def test_count_vowels_with_special_characters(self):
        """Test counting vowels in a string with special characters"""
        result = count_vowels("a!e@i#o$u%")
        assert result == 5

    def test_count_vowels_with_spaces(self):
        """Test counting vowels in a string with spaces"""
        result = count_vowels("a e i o u")
        assert result == 5

    def test_count_vowels_repeated_vowels(self):
        """Test counting repeated vowels"""
        result = count_vowels("aaaeeeiiiooouuu")
        assert result == 15

    def test_count_vowels_only_some_vowels(self):
        """Test counting when only some vowels are present"""
        result = count_vowels("apple")
        assert result == 2  # a, e

    def test_count_vowels_unicode_characters(self):
        """Test counting vowels with unicode characters"""
        result = count_vowels("café")
        assert result == 2  # a, e (é is not counted as it's not a basic vowel)

    def test_count_vowels_long_string(self):
        """Test counting vowels in a long string"""
        long_string = "a" * 1000 + "e" * 1000 + "b" * 1000
        result = count_vowels(long_string)
        assert result == 2000

    def test_count_vowels_case_insensitivity(self):
        """Test that vowel counting is case insensitive"""
        result1 = count_vowels("AEIOU")
        result2 = count_vowels("aeiou")
        result3 = count_vowels("AeIoU")
        assert result1 == result2 == result3 == 5

    def test_count_vowels_with_punctuation(self):
        """Test counting vowels with punctuation marks"""
        result = count_vowels("Hello, World! How are you?")
        assert result == 8  # e, o, o, o, a, e, o, u
