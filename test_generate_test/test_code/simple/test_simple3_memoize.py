# from advanced_functions import memoize, fibonacci_memoized
import pytest

from data.raw.simple.simple3 import fibonacci_memoized, memoize


class TestMemoize:
    """Test suite for the memoize decorator function"""

    def test_memoize_caches_results(self):
        """Test that memoize properly caches function results"""
        call_count = 0

        @memoize
        def test_func(x):
            nonlocal call_count
            call_count += 1
            return x * 2

        # First call should compute the result
        result1 = test_func(5)
        assert result1 == 10
        assert call_count == 1

        # Second call with same args should use cache
        result2 = test_func(5)
        assert result2 == 10
        assert call_count == 1  # Call count should not increase

        # Different args should trigger new computation
        result3 = test_func(10)
        assert result3 == 20
        assert call_count == 2

    def test_memoize_with_multiple_arguments(self):
        """Test memoize with functions that take multiple arguments"""
        call_count = 0

        @memoize
        def multi_arg_func(a, b, c):
            nonlocal call_count
            call_count += 1
            return a + b + c

        # Test with multiple arguments
        result1 = multi_arg_func(1, 2, 3)
        assert result1 == 6
        assert call_count == 1

        # Same arguments should use cache
        result2 = multi_arg_func(1, 2, 3)
        assert result2 == 6
        assert call_count == 1

        # Different arguments should compute again
        result3 = multi_arg_func(4, 5, 6)
        assert result3 == 15
        assert call_count == 2

    def test_memoize_with_keyword_arguments(self):
        """Test memoize with keyword arguments (should work as positional args are used for cache key)"""
        call_count = 0

        @memoize
        def kwarg_func(a, b=0):
            nonlocal call_count
            call_count += 1
            return a + b

        # Test with positional args
        result1 = kwarg_func(5)
        assert result1 == 5
        assert call_count == 1

        # Same call with different kwarg syntax should be cached differently
        result2 = kwarg_func(5, b=0)
        assert result2 == 5
        # This will be a cache miss because args tuple is different: (5,) vs (5, 0)
        assert call_count == 2

    def test_memoize_with_complex_objects(self):
        """Test memoize with complex objects as arguments"""
        call_count = 0

        @memoize
        def process_data(data):
            nonlocal call_count
            call_count += 1
            return len(data)

        # Test with list
        list_data = [1, 2, 3]
        result1 = process_data(list_data)
        assert result1 == 3
        assert call_count == 1

        # Same list should be cached
        result2 = process_data(list_data)
        assert result2 == 3
        assert call_count == 1

        # Different list (even with same content) should be cache miss
        result3 = process_data([1, 2, 3])
        assert result3 == 3
        assert call_count == 2

    def test_memoize_isolation_between_functions(self):
        """Test that different memoized functions have separate caches"""
        call_count_1 = 0
        call_count_2 = 0

        @memoize
        def func1(x):
            nonlocal call_count_1
            call_count_1 += 1
            return x * 2

        @memoize
        def func2(x):
            nonlocal call_count_2
            call_count_2 += 1
            return x * 3

        # Call both functions with same argument
        result1 = func1(5)
        result2 = func2(5)

        assert result1 == 10
        assert result2 == 15
        assert call_count_1 == 1
        assert call_count_2 == 1

        # Call again - both should use their own caches
        result1_again = func1(5)
        result2_again = func2(5)

        assert result1_again == 10
        assert result2_again == 15
        assert call_count_1 == 1  # No increase
        assert call_count_2 == 1  # No increase

    def test_memoize_with_none_and_false_values(self):
        """Test memoize with None and False return values"""
        call_count = 0

        @memoize
        def returns_special_values(x):
            nonlocal call_count
            call_count += 1
            if x == 1:
                return None
            elif x == 2:
                return False
            else:
                return True

        # Test with None return value
        result1 = returns_special_values(1)
        assert result1 is None
        assert call_count == 1

        # Should be cached
        result1_again = returns_special_values(1)
        assert result1_again is None
        assert call_count == 1

        # Test with False return value
        result2 = returns_special_values(2)
        assert result2 is False
        assert call_count == 2

        # Should be cached
        result2_again = returns_special_values(2)
        assert result2_again is False
        assert call_count == 2

    def test_memoize_practical_example_fibonacci(self):
        """Test the practical fibonacci_memoized function from the source code"""
        # Test base cases
        assert fibonacci_memoized(0) == 0
        assert fibonacci_memoized(1) == 1

        # Test recursive case - this should be efficient due to memoization
        assert fibonacci_memoized(5) == 5
        assert fibonacci_memoized(10) == 55

        # Test that larger values work (memoization makes this feasible)
        assert fibonacci_memoized(20) == 6765

    def test_memoize_with_exceptions(self):
        """Test that memoize doesn't cache exceptions"""
        call_count = 0

        @memoize
        def sometimes_fails(x):
            nonlocal call_count
            call_count += 1
            if x < 0:
                raise ValueError("Negative values not allowed")
            return x * 2

        # Normal call
        result1 = sometimes_fails(5)
        assert result1 == 10
        assert call_count == 1

        # Cached call
        result2 = sometimes_fails(5)
        assert result2 == 10
        assert call_count == 1

        # Call that raises exception
        with pytest.raises(ValueError, match="Negative values not allowed"):
            sometimes_fails(-1)
        assert call_count == 2

        # Exception call should not be cached - should raise again
        with pytest.raises(ValueError, match="Negative values not allowed"):
            sometimes_fails(-1)
        assert call_count == 3  # Should call again, not cache exception

    def test_memoize_cache_persistence(self):
        """Test that cache persists across multiple calls"""
        call_count = 0

        @memoize
        def persistent_func(x):
            nonlocal call_count
            call_count += 1
            return x**2

        # Make several calls with different arguments
        results = []
        for i in range(5):
            results.append(persistent_func(i))

        assert call_count == 5  # All should be computed

        # Call the same arguments again
        for i in range(5):
            results.append(persistent_func(i))

        assert call_count == 5  # No additional calls - all cached

        # Verify results are correct
        assert results == [0, 1, 4, 9, 16, 0, 1, 4, 9, 16]
