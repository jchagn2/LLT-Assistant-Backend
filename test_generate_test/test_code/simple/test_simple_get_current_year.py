import inspect

# from math_functions import get_current_year
import pytest

from data.raw.simple.simple import get_current_year


class TestGetCurrentYear:
    """Test cases for the get_current_year function."""

    def test_returns_correct_year(self):
        """Test that the function returns the expected fixed year value."""
        result = get_current_year()
        assert result == 2024
        assert isinstance(result, int)

    def test_return_type_is_integer(self):
        """Test that the return value is of integer type."""
        result = get_current_year()
        assert type(result) is int

    def test_returns_positive_year(self):
        """Test that the returned year is a positive number."""
        result = get_current_year()
        assert result > 0

    def test_returns_reasonable_year(self):
        """Test that the returned year is within a reasonable range (2000-2100)."""
        result = get_current_year()
        assert 2000 <= result <= 2100

    def test_consistent_return_value(self):
        """Test that multiple calls return the same value (function is deterministic)."""
        first_call = get_current_year()
        second_call = get_current_year()
        third_call = get_current_year()

        assert first_call == second_call == third_call == 2024

    def test_no_parameters_required(self):
        """Test that the function can be called without any parameters."""
        result = get_current_year()
        assert result is not None

    def test_year_is_four_digits(self):
        """Test that the returned year has exactly 4 digits."""
        result = get_current_year()
        assert len(str(result)) == 4


# Additional edge case tests
def test_function_is_callable():
    """Test that the function is callable and doesn't raise exceptions."""
    # This should not raise any exceptions
    result = get_current_year()
    assert result is not None


def test_function_has_correct_signature():
    """Test that the function has the expected signature (no parameters)."""
    sig = inspect.signature(get_current_year)
    assert len(sig.parameters) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
