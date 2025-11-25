# from math_functions import sum_list
import pytest

from data.raw.simple.simple import sum_list


class TestSumList:
    """Test cases for the sum_list function"""

    def test_sum_list_typical_case(self):
        """Test typical case with positive integers"""
        numbers = [1, 2, 3, 4, 5]
        result = sum_list(numbers)
        assert result == 15
        assert isinstance(result, int)

    def test_sum_list_negative_numbers(self):
        """Test with negative integers"""
        numbers = [-1, -2, -3, -4, -5]
        result = sum_list(numbers)
        assert result == -15

    def test_sum_list_mixed_positive_negative(self):
        """Test with mix of positive and negative integers"""
        numbers = [10, -5, 3, -2, 8]
        result = sum_list(numbers)
        assert result == 14

    def test_sum_list_single_element(self):
        """Test with single element list"""
        numbers = [42]
        result = sum_list(numbers)
        assert result == 42

    def test_sum_list_empty_list(self):
        """Test with empty list"""
        numbers = []
        result = sum_list(numbers)
        assert result == 0

    def test_sum_list_zeros(self):
        """Test with zeros"""
        numbers = [0, 0, 0, 0]
        result = sum_list(numbers)
        assert result == 0

    def test_sum_list_large_numbers(self):
        """Test with large integers"""
        numbers = [1000000, 2000000, 3000000]
        result = sum_list(numbers)
        assert result == 6000000

    def test_sum_list_duplicate_numbers(self):
        """Test with duplicate numbers"""
        numbers = [5, 5, 5, 5, 5]
        result = sum_list(numbers)
        assert result == 25

    def test_sum_list_sequential_numbers(self):
        """Test with sequential numbers"""
        numbers = list(range(1, 101))  # 1 to 100
        result = sum_list(numbers)
        assert result == 5050  # Sum of first 100 natural numbers

    def test_sum_list_preserves_original_list(self):
        """Test that original list is not modified"""
        original_numbers = [1, 2, 3]
        numbers = original_numbers.copy()
        result = sum_list(numbers)
        assert numbers == original_numbers  # Original list unchanged
        assert result == 6


# Edge cases with invalid inputs
class TestSumListEdgeCases:
    """Edge case tests for sum_list function"""

    def test_sum_list_with_floats_raises_error(self):
        """Test that function raises appropriate error with float inputs"""
        numbers = [1.5, 2.5, 3.5]
        with pytest.raises(TypeError):
            sum_list(numbers)

    def test_sum_list_with_strings_raises_error(self):
        """Test that function raises appropriate error with string inputs"""
        numbers = ["1", "2", "3"]
        with pytest.raises(TypeError):
            sum_list(numbers)

    def test_sum_list_with_mixed_types_raises_error(self):
        """Test that function raises appropriate error with mixed type inputs"""
        numbers = [1, "2", 3]
        with pytest.raises(TypeError):
            sum_list(numbers)

    def test_sum_list_with_none_raises_error(self):
        """Test that function raises appropriate error with None in list"""
        numbers = [1, None, 3]
        with pytest.raises(TypeError):
            sum_list(numbers)

    def test_sum_list_none_input_raises_error(self):
        """Test that function raises appropriate error with None as input"""
        with pytest.raises(TypeError):
            sum_list(None)


# Performance and behavior tests
class TestSumListBehavior:
    """Behavioral tests for sum_list function"""

    def test_sum_list_return_type(self):
        """Test that return type is always integer"""
        test_cases = [[1, 2, 3], [-1, -2, -3], [0, 0, 0], [1000000], []]

        for numbers in test_cases:
            result = sum_list(numbers)
            assert isinstance(
                result, int
            ), f"Expected int, got {type(result)} for input {numbers}"

    def test_sum_list_commutative_property(self):
        """Test that sum is commutative (order doesn't matter)"""
        numbers1 = [1, 2, 3, 4, 5]
        numbers2 = [5, 4, 3, 2, 1]  # Reverse order
        numbers3 = [3, 1, 5, 2, 4]  # Random order

        result1 = sum_list(numbers1)
        result2 = sum_list(numbers2)
        result3 = sum_list(numbers3)

        assert result1 == result2 == result3 == 15
