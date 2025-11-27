# from math_functions import fibonacci
import pytest

from data.raw.simple.simple import fibonacci


class TestFibonacci:
    """Test cases for the fibonacci function."""

    def test_fibonacci_positive_numbers(self):
        """Test fibonacci function with typical positive numbers."""
        # Test first 5 Fibonacci numbers
        assert fibonacci(5) == [0, 1, 1, 2, 3]

        # Test first 10 Fibonacci numbers
        assert fibonacci(10) == [0, 1, 1, 2, 3, 5, 8, 13, 21, 34]

        # Test single number case
        assert fibonacci(1) == [0]

        # Test two numbers case
        assert fibonacci(2) == [0, 1]

    def test_fibonacci_edge_cases(self):
        """Test fibonacci function with edge cases."""
        # Test n=0 (should return empty list)
        assert fibonacci(0) == []

        # Test n=3 (small valid sequence)
        assert fibonacci(3) == [0, 1, 1]

        # Test n=4
        assert fibonacci(4) == [0, 1, 1, 2]

    def test_fibonacci_large_number(self):
        """Test fibonacci function with a larger number."""
        # Test first 15 Fibonacci numbers
        expected = [0, 1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144, 233, 377]
        assert fibonacci(15) == expected

    def test_fibonacci_negative_input(self):
        """Test fibonacci function with negative input."""
        # Negative numbers should return empty list
        assert fibonacci(-1) == []
        assert fibonacci(-5) == []
        assert fibonacci(-100) == []

    def test_fibonacci_property_based(self):
        """Test mathematical properties of Fibonacci sequence."""
        # Test that each number is sum of previous two (for sequences longer than 2)
        result = fibonacci(10)
        for i in range(2, len(result)):
            assert result[i] == result[i - 1] + result[i - 2]

        # Test that sequence starts with 0, 1
        result = fibonacci(5)
        assert result[0] == 0
        assert result[1] == 1

    def test_fibonacci_length_correctness(self):
        """Test that the returned list has exactly n elements."""
        for n in [0, 1, 2, 5, 10, 20]:
            result = fibonacci(n)
            assert len(result) == n

    def test_fibonacci_type_safety(self):
        """Test that function handles different input types appropriately."""
        # Should work with integer inputs
        assert isinstance(fibonacci(5), list)
        assert all(isinstance(x, int) for x in fibonacci(5))

        # Float inputs that are whole numbers should work (due to Python's typing)
        # But let's test the behavior
        assert fibonacci(5.0) == [0, 1, 1, 2, 3]

    def test_fibonacci_very_small_sequences(self):
        """Test very small sequence lengths."""
        # Test various small n values
        test_cases = [
            (0, []),
            (1, [0]),
            (2, [0, 1]),
            (3, [0, 1, 1]),
            (4, [0, 1, 1, 2]),
            (6, [0, 1, 1, 2, 3, 5]),
        ]

        for n, expected in test_cases:
            assert fibonacci(n) == expected, f"Failed for n={n}"
