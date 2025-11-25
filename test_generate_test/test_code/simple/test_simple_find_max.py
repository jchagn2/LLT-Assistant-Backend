# from math_functions import find_max
import pytest

from data.raw.simple.simple import find_max


class TestFindMax:
    """Test cases for the find_max function"""

    def test_find_max_typical_case(self):
        """Test typical case with multiple positive numbers"""
        numbers = [1, 5, 3, 9, 2]
        result = find_max(numbers)
        assert result == 9

    def test_find_max_negative_numbers(self):
        """Test with negative numbers"""
        numbers = [-5, -2, -10, -1]
        result = find_max(numbers)
        assert result == -1

    def test_find_max_mixed_numbers(self):
        """Test with mixed positive and negative numbers"""
        numbers = [-3, 0, 7, -10, 5]
        result = find_max(numbers)
        assert result == 7

    def test_find_max_single_element(self):
        """Test with single element list"""
        numbers = [42]
        result = find_max(numbers)
        assert result == 42

    def test_find_max_duplicate_max(self):
        """Test with duplicate maximum values"""
        numbers = [5, 3, 5, 2, 5]
        result = find_max(numbers)
        assert result == 5

    def test_find_max_large_numbers(self):
        """Test with large numbers"""
        numbers = [1000000, 999999, 1000001, 1000000]
        result = find_max(numbers)
        assert result == 1000001

    def test_find_max_zeros(self):
        """Test with zeros"""
        numbers = [0, 0, 0, 0]
        result = find_max(numbers)
        assert result == 0

    def test_find_max_float_numbers(self):
        """Test with float numbers (should work since int is subset of float)"""
        numbers = [1.5, 3.7, 2.1, 4.9]
        result = find_max(numbers)
        assert result == 4.9

    def test_find_max_ordered_ascending(self):
        """Test with numbers in ascending order"""
        numbers = [1, 2, 3, 4, 5]
        result = find_max(numbers)
        assert result == 5

    def test_find_max_ordered_descending(self):
        """Test with numbers in descending order"""
        numbers = [5, 4, 3, 2, 1]
        result = find_max(numbers)
        assert result == 5

    def test_find_max_with_negative_zero(self):
        """Test with negative zero"""
        numbers = [-0, 0, -5, 3]
        result = find_max(numbers)
        assert result == 3

    def test_find_max_large_list(self):
        """Test with a larger list"""
        numbers = list(range(1, 101))  # 1 to 100
        result = find_max(numbers)
        assert result == 100

    def test_find_max_edge_case_minimum(self):
        """Test with minimum integer values"""
        numbers = [-2147483648, -2147483647, 0]
        result = find_max(numbers)
        assert result == 0

    def test_find_max_all_same(self):
        """Test with all elements being the same"""
        numbers = [7, 7, 7, 7, 7]
        result = find_max(numbers)
        assert result == 7

    def test_find_max_with_bool_values(self):
        """Test with boolean values (True=1, False=0)"""
        numbers = [True, False, 2, 1]
        result = find_max(numbers)
        assert result == 2  # Since True=1, False=0


# Error handling tests (the function assumes non-empty list)
def test_find_max_empty_list():
    """Test that empty list raises appropriate error"""
    numbers = []
    with pytest.raises(ValueError) as exc_info:
        find_max(numbers)
    assert "max() arg is an empty sequence" in str(exc_info.value)


# Property-based style test
def test_find_max_always_greater_or_equal():
    """Test that max is always greater than or equal to all elements"""
    numbers = [3, 1, 4, 1, 5, 9, 2, 6, 5]
    max_value = find_max(numbers)

    for num in numbers:
        assert max_value >= num


def test_find_max_is_in_original_list():
    """Test that the maximum value is actually in the original list"""
    numbers = [10, 20, 30, 40, 50]
    max_value = find_max(numbers)

    assert max_value in numbers
