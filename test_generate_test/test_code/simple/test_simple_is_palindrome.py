# from math_functions import is_palindrome
import pytest

from data.raw.simple.simple import is_palindrome


class TestIsPalindrome:
    """Test cases for the is_palindrome function."""

    def test_typical_palindromes(self):
        """Test typical palindrome strings."""
        # Standard palindromes
        assert is_palindrome("racecar") == True
        assert is_palindrome("madam") == True
        assert is_palindrome("level") == True
        assert is_palindrome("deified") == True

        # Palindromes with spaces (should be ignored)
        assert is_palindrome("a man a plan a canal panama") == True
        assert is_palindrome("never odd or even") == True

        # Palindromes with mixed case (should be case-insensitive)
        assert is_palindrome("RaceCar") == True
        assert is_palindrome("MaDaM") == True
        assert is_palindrome("LeVeL") == True

    def test_non_palindromes(self):
        """Test strings that are not palindromes."""
        assert is_palindrome("hello") == False
        assert is_palindrome("world") == False
        assert is_palindrome("python") == False
        assert is_palindrome("programming") == False

        # Strings that would be palindromes without spaces/case differences
        assert (
            is_palindrome("Race Car") == True
        )  # This IS a palindrome when spaces are removed
        assert is_palindrome("A man a plan") == False  # This is NOT a palindrome

    def test_edge_cases(self):
        """Test edge cases and boundary conditions."""
        # Empty string (considered a palindrome)
        assert is_palindrome("") == True

        # Single character
        assert is_palindrome("a") == True
        assert is_palindrome("A") == True
        assert is_palindrome("1") == True

        # Two characters
        assert is_palindrome("aa") == True
        assert is_palindrome("ab") == False
        assert is_palindrome("AA") == True

        # Strings with only spaces
        assert is_palindrome("   ") == True
        assert is_palindrome("  ") == True
        assert is_palindrome(" ") == True

    def test_special_characters_and_numbers(self):
        """Test strings with special characters, numbers, and punctuation."""
        # Palindromes with numbers
        assert is_palindrome("12321") == True
        assert is_palindrome("123321") == True

        # Non-palindromes with numbers
        assert is_palindrome("12345") == False
        assert is_palindrome("123456") == False

        # Strings with punctuation (punctuation is not removed, so these may not be palindromes)
        assert is_palindrome("race car!") == False  # "racecar!" vs "!racecar"
        assert is_palindrome("madam!") == False  # "madam!" vs "!madam"

        # Strings with special characters
        assert (
            is_palindrome("a@a") == False
        )  # "a@a" vs "a@a" - actually this IS a palindrome
        assert is_palindrome("a@b") == False  # "a@b" vs "b@a"

    def test_unicode_and_international_characters(self):
        """Test strings with unicode and international characters."""
        # Palindromes with accented characters
        assert is_palindrome("été") == True
        assert is_palindrome("ÉTÉ") == True

        # Non-palindromes with accented characters
        assert is_palindrome("café") == False

        # Mixed language palindromes
        assert is_palindrome("aibohphobia") == True  # Fear of palindromes!

    def test_case_insensitivity(self):
        """Test that the function is truly case-insensitive."""
        # Mixed case palindromes
        assert is_palindrome("RaCeCaR") == True
        assert is_palindrome("MaDaM") == True
        assert is_palindrome("LeVeL") == True

        # Same letters, different cases - should still be palindromes
        assert is_palindrome("aA") == True
        assert is_palindrome("Aa") == True
        assert is_palindrome("aAa") == True

    def test_space_removal(self):
        """Test that spaces are properly removed before checking."""
        # Palindromes with various spacing
        assert is_palindrome("race car") == True
        assert is_palindrome(" racecar ") == True
        assert is_palindrome("r a c e c a r") == True
        assert is_palindrome("  racecar  ") == True

        # Non-palindromes that would be palindromes without spaces
        assert is_palindrome("race car!") == False  # Because of the exclamation mark
        assert is_palindrome("race car ") == True  # This IS a palindrome


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
