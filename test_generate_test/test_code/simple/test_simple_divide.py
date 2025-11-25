# from math_functions import divide
import pytest

from data.raw.simple.simple import divide


class TestDivide:
    """Test cases for the divide function"""

    def test_divide_positive_numbers(self):
        """Test dividing two positive integers"""
        result = divide(10, 2)
        assert result == 5.0
        assert isinstance(result, float)

    def test_divide_negative_numbers(self):
        """Test dividing two negative integers"""
        result = divide(-10, -2)
        assert result == 5.0

    def test_divide_mixed_signs(self):
        """Test dividing numbers with mixed signs"""
        result1 = divide(10, -2)
        assert result1 == -5.0

        result2 = divide(-10, 2)
        assert result2 == -5.0

    def test_divide_zero_numerator(self):
        """Test dividing zero by a non-zero number"""
        result = divide(0, 5)
        assert result == 0.0

    def test_divide_fractional_result(self):
        """Test division that results in fractional numbers"""
        result = divide(5, 2)
        assert result == 2.5

        result = divide(1, 3)
        assert abs(result - 0.333333) < 0.000001

    def test_divide_large_numbers(self):
        """Test dividing large numbers"""
        result = divide(1000000, 1000)
        assert result == 1000.0

    def test_divide_by_one(self):
        """Test dividing by 1"""
        result = divide(42, 1)
        assert result == 42.0

    def test_divide_same_number(self):
        """Test dividing a number by itself"""
        result = divide(7, 7)
        assert result == 1.0

    def test_divide_by_zero_raises_error(self):
        """Test that dividing by zero raises ZeroDivisionError"""
        with pytest.raises(ZeroDivisionError):
            divide(10, 0)

    def test_divide_zero_by_zero_raises_error(self):
        """Test that dividing zero by zero raises ZeroDivisionError"""
        with pytest.raises(ZeroDivisionError):
            divide(0, 0)

    def test_divide_result_type(self):
        """Test that the result is always a float"""
        # Even when result is whole number, it should return float
        result = divide(4, 2)
        assert isinstance(result, float)
        assert result == 2.0

    def test_divide_very_small_numbers(self):
        """Test dividing very small numbers"""
        result = divide(1, 1000000)
        assert result == 0.000001

    def test_divide_odd_even_combinations(self):
        """Test various odd/even number combinations"""
        # Even divided by even
        result = divide(8, 4)
        assert result == 2.0

        # Odd divided by odd
        result = divide(9, 3)
        assert result == 3.0

        # Even divided by odd
        result = divide(10, 3)
        assert abs(result - 3.333333) < 0.000001

        # Odd divided by even
        result = divide(7, 2)
        assert result == 3.5
