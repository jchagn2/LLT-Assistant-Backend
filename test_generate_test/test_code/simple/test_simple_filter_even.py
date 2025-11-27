# from math_functions import filter_even
import pytest

from data.raw.simple.simple import filter_even


class TestFilterEven:
    """Test cases for the filter_even function"""

    def test_basic_even_numbers(self):
        """Test filtering basic even numbers"""
        numbers = [1, 2, 3, 4, 5, 6]
        expected = [2, 4, 6]
        result = filter_even(numbers)
        assert result == expected
        assert isinstance(result, list)

    def test_all_odd_numbers(self):
        """Test filtering when all numbers are odd"""
        numbers = [1, 3, 5, 7, 9]
        expected = []
        result = filter_even(numbers)
        assert result == expected

    def test_all_even_numbers(self):
        """Test filtering when all numbers are even"""
        numbers = [2, 4, 6, 8, 10]
        expected = [2, 4, 6, 8, 10]
        result = filter_even(numbers)
        assert result == expected

    def test_empty_list(self):
        """Test filtering an empty list"""
        numbers = []
        expected = []
        result = filter_even(numbers)
        assert result == expected

    def test_negative_even_numbers(self):
        """Test filtering negative even numbers"""
        numbers = [-4, -3, -2, -1, 0, 1, 2, 3, 4]
        expected = [-4, -2, 0, 2, 4]
        result = filter_even(numbers)
        assert result == expected

    def test_zero_in_list(self):
        """Test that zero is correctly identified as even"""
        numbers = [0, 1, 2, 3]
        expected = [0, 2]
        result = filter_even(numbers)
        assert result == expected

    def test_large_numbers(self):
        """Test filtering with large numbers"""
        numbers = [1000000, 1000001, 999999, 1000002]
        expected = [1000000, 1000002]
        result = filter_even(numbers)
        assert result == expected

    def test_duplicate_even_numbers(self):
        """Test filtering with duplicate even numbers"""
        numbers = [2, 2, 4, 4, 6, 6, 1, 3, 5]
        expected = [2, 2, 4, 4, 6, 6]
        result = filter_even(numbers)
        assert result == expected

    def test_preserves_order(self):
        """Test that the function preserves the original order"""
        numbers = [3, 8, 1, 6, 9, 4, 7, 2]
        expected = [8, 6, 4, 2]
        result = filter_even(numbers)
        assert result == expected

    def test_single_element_even(self):
        """Test filtering a list with single even element"""
        numbers = [42]
        expected = [42]
        result = filter_even(numbers)
        assert result == expected

    def test_single_element_odd(self):
        """Test filtering a list with single odd element"""
        numbers = [43]
        expected = []
        result = filter_even(numbers)
        assert result == expected

    def test_very_large_even_number(self):
        """Test filtering with very large even number"""
        numbers = [10**18, 10**18 + 1]
        expected = [10**18]
        result = filter_even(numbers)
        assert result == expected

    def test_mixed_positive_negative_zero(self):
        """Test filtering with mixed positive, negative numbers and zero"""
        numbers = [-5, -4, -3, -2, -1, 0, 1, 2, 3, 4, 5]
        expected = [-4, -2, 0, 2, 4]
        result = filter_even(numbers)
        assert result == expected

    def test_returns_new_list(self):
        """Test that the function returns a new list and doesn't modify the original"""
        original = [1, 2, 3, 4, 5]
        numbers = original.copy()
        result = filter_even(numbers)

        # Verify result is correct
        assert result == [2, 4]

        # Verify original list is unchanged
        assert numbers == original

        # Verify it's a different list object
        assert result is not numbers
