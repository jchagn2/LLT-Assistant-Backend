# from math_functions import add
import pytest

from data.raw.simple.simple import add


class TestAdd:
    """Test cases for the add function."""

    def test_add_positive_numbers(self):
        """Test adding two positive numbers."""
        assert add(2, 3) == 5
        assert add(10, 15) == 25
        assert add(100, 200) == 300

    def test_add_negative_numbers(self):
        """Test adding two negative numbers."""
        assert add(-2, -3) == -5
        assert add(-10, -15) == -25
        assert add(-100, -200) == -300

    def test_add_mixed_sign_numbers(self):
        """Test adding numbers with different signs."""
        assert add(5, -3) == 2
        assert add(-5, 3) == -2
        assert add(-10, 15) == 5
        assert add(10, -15) == -5

    def test_add_zero(self):
        """Test adding zero to numbers."""
        assert add(0, 0) == 0
        assert add(5, 0) == 5
        assert add(0, 5) == 5
        assert add(-5, 0) == -5
        assert add(0, -5) == -5

    def test_add_large_numbers(self):
        """Test adding large numbers."""
        assert add(1000000, 2000000) == 3000000
        assert add(-1000000, -2000000) == -3000000
        assert add(2147483647, 1) == 2147483648  # Near 32-bit integer limit

    def test_add_same_number(self):
        """Test adding a number to itself."""
        assert add(5, 5) == 10
        assert add(-3, -3) == -6
        assert add(0, 0) == 0

    def test_add_commutative_property(self):
        """Test that addition is commutative (a + b = b + a)."""
        a, b = 7, 12
        assert add(a, b) == add(b, a)

        a, b = -7, 12
        assert add(a, b) == add(b, a)

        a, b = -7, -12
        assert add(a, b) == add(b, a)

    def test_add_associative_property(self):
        """Test that addition is associative ((a + b) + c = a + (b + c))."""
        a, b, c = 2, 3, 4
        assert add(add(a, b), c) == add(a, add(b, c))

        a, b, c = -2, 3, -4
        assert add(add(a, b), c) == add(a, add(b, c))

    def test_add_identity_property(self):
        """Test that adding zero doesn't change the number."""
        numbers = [0, 1, -1, 100, -100, 999, -999]
        for num in numbers:
            assert add(num, 0) == num
            assert add(0, num) == num

    def test_add_boundary_values(self):
        """Test addition with boundary values."""
        # Small numbers
        assert add(1, 1) == 2
        assert add(-1, -1) == -2

        # Numbers near zero
        assert add(1, -1) == 0
        assert add(-1, 1) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
