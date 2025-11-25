# from math_functions import factorial
import pytest

from data.raw.simple.simple import factorial


class TestFactorial:
    """Test cases for the factorial function"""

    def test_factorial_zero(self):
        """Test factorial of 0 (edge case)"""
        assert factorial(0) == 1

    def test_factorial_one(self):
        """Test factorial of 1 (edge case)"""
        assert factorial(1) == 1

    def test_factorial_small_positive_numbers(self):
        """Test factorial of small positive numbers (typical scenarios)"""
        assert factorial(2) == 2
        assert factorial(3) == 6
        assert factorial(4) == 24
        assert factorial(5) == 120
        assert factorial(6) == 720

    def test_factorial_medium_positive_numbers(self):
        """Test factorial of medium positive numbers"""
        assert factorial(7) == 5040
        assert factorial(8) == 40320
        assert factorial(10) == 3628800

    def test_factorial_negative_number(self):
        """Test factorial with negative input (error handling)"""
        with pytest.raises(ValueError) as exc_info:
            factorial(-1)
        assert "Factorial is not defined for negative numbers" in str(exc_info.value)

        with pytest.raises(ValueError):
            factorial(-5)

    def test_factorial_large_number(self):
        """Test factorial with a larger number"""
        assert factorial(12) == 479001600

    def test_factorial_consistency(self):
        """Test that factorial(n) = n * factorial(n-1) for n > 1"""
        for n in range(2, 10):
            assert factorial(n) == n * factorial(n - 1)

    def test_factorial_boundary_values(self):
        """Test boundary values around 0 and 1"""
        # Test that factorial(0) and factorial(1) are handled correctly
        assert factorial(0) == 1
        assert factorial(1) == 1
        assert factorial(2) == 2  # Verify the transition works correctly
