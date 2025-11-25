# from math_functions import subtract
import pytest

from data.raw.simple.simple import subtract


class TestSubtract:
    """Test cases for the subtract function."""

    def test_subtract_positive_numbers(self):
        """Test subtracting two positive numbers."""
        assert subtract(5, 3) == 2
        assert subtract(10, 7) == 3
        assert subtract(100, 50) == 50

    def test_subtract_negative_numbers(self):
        """Test subtracting negative numbers."""
        assert subtract(-5, -3) == -2
        assert subtract(-10, -7) == -3
        assert subtract(-100, -50) == -50

    def test_subtract_mixed_sign_numbers(self):
        """Test subtracting numbers with mixed signs."""
        assert subtract(5, -3) == 8
        assert subtract(-5, 3) == -8
        assert subtract(0, -5) == 5
        assert subtract(-10, 5) == -15

    def test_subtract_zero(self):
        """Test subtracting zero."""
        assert subtract(5, 0) == 5
        assert subtract(0, 5) == -5
        assert subtract(0, 0) == 0

    def test_subtract_large_numbers(self):
        """Test subtracting large numbers."""
        assert subtract(1000000, 500000) == 500000
        assert subtract(-1000000, 500000) == -1500000

    def test_subtract_identity_property(self):
        """Test that subtracting a number from itself gives zero."""
        assert subtract(5, 5) == 0
        assert subtract(-10, -10) == 0
        assert subtract(0, 0) == 0

    def test_subtract_commutative_property(self):
        """Test that subtraction is not commutative."""
        # a - b should not equal b - a (except when a == b)
        assert subtract(5, 3) != subtract(3, 5)
        assert subtract(10, 2) != subtract(2, 10)

    def test_subtract_boundary_values(self):
        """Test with boundary values."""
        # Using sys.maxsize would be better but keeping it simple
        assert subtract(999999, 999998) == 1
        assert subtract(-999999, -999998) == -1

    def test_subtract_result_types(self):
        """Test that results maintain integer type."""
        result = subtract(10, 3)
        assert isinstance(result, int)
        assert subtract(-5, -2) == -3
        assert isinstance(subtract(-5, -2), int)


# Edge cases and error handling tests
class TestSubtractEdgeCases:
    """Test edge cases for the subtract function."""

    def test_subtract_very_small_difference(self):
        """Test subtracting numbers that are very close."""
        assert subtract(100, 99) == 1
        assert subtract(1, 1) == 0
        assert subtract(2, 1) == 1

    def test_subtract_negative_result(self):
        """Test cases where result should be negative."""
        assert subtract(3, 5) == -2
        assert subtract(0, 1) == -1
        assert subtract(10, 20) == -10

    def test_subtract_positive_result(self):
        """Test cases where result should be positive."""
        assert subtract(5, 3) == 2
        assert subtract(10, 5) == 5
        assert subtract(1, 0) == 1

    def test_subtract_same_number(self):
        """Test subtracting the same number multiple times."""
        assert subtract(10, 5) == 5
        assert subtract(5, 5) == 0
        assert subtract(subtract(10, 5), 2) == 3


# Parameterized tests for comprehensive coverage
@pytest.mark.parametrize(
    "a,b,expected",
    [
        (10, 5, 5),  # Basic positive subtraction
        (5, 10, -5),  # Result negative
        (0, 0, 0),  # Both zeros
        (-5, -3, -2),  # Both negatives
        (5, -3, 8),  # Positive minus negative
        (-5, 3, -8),  # Negative minus positive
        (100, 99, 1),  # Close numbers
        (999, 1, 998),  # Large difference
        (1, 1, 0),  # Identity case
    ],
)
def test_subtract_parameterized(a, b, expected):
    """Parameterized test for various subtraction scenarios."""
    assert subtract(a, b) == expected


# Property-based testing style tests
class TestSubtractProperties:
    """Test mathematical properties of subtraction."""

    def test_subtract_inverse_of_addition(self):
        """Test that (a - b) + b should equal a."""
        test_cases = [(5, 3), (10, 7), (-5, -3), (0, 5)]
        for a, b in test_cases:
            result = subtract(a, b)
            assert result + b == a

    def test_subtract_zero_identity(self):
        """Test that subtracting zero doesn't change the number."""
        test_numbers = [5, -5, 0, 100, -100]
        for num in test_numbers:
            assert subtract(num, 0) == num

    def test_subtract_self_zero(self):
        """Test that subtracting a number from itself gives zero."""
        test_numbers = [5, -5, 0, 100, -100]
        for num in test_numbers:
            assert subtract(num, num) == 0
