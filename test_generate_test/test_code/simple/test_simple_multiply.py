import pytest

from data.raw.simple.simple import add, multiply


class TestMultiply:
    """Test cases for the multiply function"""

    def test_multiply_positive_numbers(self):
        """Test multiplying two positive integers"""
        assert multiply(5, 3) == 15
        assert multiply(10, 10) == 100
        assert multiply(1, 100) == 100

    def test_multiply_negative_numbers(self):
        """Test multiplying negative integers"""
        assert multiply(-5, 3) == -15
        assert multiply(5, -3) == -15
        assert multiply(-5, -3) == 15

    def test_multiply_with_zero(self):
        """Test multiplying with zero"""
        assert multiply(0, 5) == 0
        assert multiply(5, 0) == 0
        assert multiply(0, 0) == 0
        assert multiply(0, -5) == 0

    def test_multiply_large_numbers(self):
        """Test multiplying large integers"""
        assert multiply(1000000, 1000000) == 1000000000000
        assert multiply(-1000000, 1000000) == -1000000000000

    def test_multiply_identity_property(self):
        """Test identity property of multiplication"""
        assert multiply(1, 42) == 42
        assert multiply(42, 1) == 42

    def test_multiply_commutative_property(self):
        """Test commutative property of multiplication"""
        assert multiply(7, 8) == multiply(8, 7)
        assert multiply(-3, 4) == multiply(4, -3)

    def test_multiply_edge_cases(self):
        """Test edge cases and boundary values"""
        # Minimum integer values (Python integers have no fixed minimum)
        assert multiply(1, -999999999) == -999999999

        # Single digit numbers
        assert multiply(9, 9) == 81
        assert multiply(0, 9) == 0

    def test_multiply_negative_edge_cases(self):
        """Test edge cases with negative numbers"""
        assert multiply(-1, 1) == -1
        assert multiply(1, -1) == -1
        assert multiply(-1, -1) == 1

    def test_multiply_sequential_operations(self):
        """Test sequential multiplication operations"""
        # Chain of multiplications
        result = multiply(2, 3)
        result = multiply(result, 4)
        assert result == 24

        # Multiple operations in sequence
        assert multiply(multiply(2, 3), multiply(4, 5)) == 120

    def test_multiply_with_other_functions(self):
        """Test multiply function in combination with other math functions"""
        # This test demonstrates how multiply can work with other functions
        # from the same module (though we're only testing multiply)

        # Combined operation: (a + b) * c
        a, b, c = 2, 3, 4
        result = multiply(add(a, b), c)
        assert result == 20

    def test_multiply_return_type(self):
        """Test that multiply returns integer type"""
        result = multiply(3, 4)
        assert isinstance(result, int)

        result = multiply(-3, 4)
        assert isinstance(result, int)

        result = multiply(0, 5)
        assert isinstance(result, int)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
