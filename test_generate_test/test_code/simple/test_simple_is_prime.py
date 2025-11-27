# from math_functions import is_prime
import pytest

from data.raw.simple.simple import is_prime


class TestIsPrime:
    """Test cases for the is_prime function"""

    def test_prime_numbers(self):
        """Test known prime numbers"""
        primes = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47]
        for prime in primes:
            assert is_prime(prime) == True, f"{prime} should be prime"

    def test_non_prime_numbers(self):
        """Test known non-prime numbers"""
        non_primes = [4, 6, 8, 9, 10, 12, 14, 15, 16, 18, 20, 21, 22, 24, 25]
        for non_prime in non_primes:
            assert is_prime(non_prime) == False, f"{non_prime} should not be prime"

    def test_edge_cases(self):
        """Test edge cases and boundary values"""
        # Numbers less than or equal to 1
        assert is_prime(1) == False, "1 should not be prime"
        assert is_prime(0) == False, "0 should not be prime"
        assert is_prime(-1) == False, "-1 should not be prime"
        assert is_prime(-5) == False, "-5 should not be prime"

        # Even numbers greater than 2
        assert is_prime(4) == False, "4 should not be prime"
        assert is_prime(100) == False, "100 should not be prime"

    def test_large_prime_numbers(self):
        """Test larger prime numbers"""
        large_primes = [101, 103, 107, 109, 113, 127, 131, 137, 139, 149]
        for prime in large_primes:
            assert is_prime(prime) == True, f"{prime} should be prime"

    def test_large_non_prime_numbers(self):
        """Test larger non-prime numbers"""
        large_non_primes = [100, 102, 104, 105, 106, 108, 110, 111, 112, 114]
        for non_prime in large_non_primes:
            assert is_prime(non_prime) == False, f"{non_prime} should not be prime"

    def test_square_numbers(self):
        """Test perfect squares (which are never prime except 1, but 1 is handled)"""
        squares = [4, 9, 16, 25, 36, 49, 64, 81, 100]
        for square in squares:
            assert (
                is_prime(square) == False
            ), f"{square} (perfect square) should not be prime"

    def test_negative_numbers(self):
        """Test various negative numbers"""
        negatives = [-2, -3, -10, -100, -1000]
        for negative in negatives:
            assert (
                is_prime(negative) == False
            ), f"{negative} (negative number) should not be prime"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
