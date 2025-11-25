import math

import pytest

# from complex_functions import safe_convert_to_int
from data.raw.simple.simple2 import safe_convert_to_int


class TestSafeConvertToInt:
    """Test cases for safe_convert_to_int function"""

    def test_valid_integer_string(self):
        """Test conversion of valid integer strings"""
        assert safe_convert_to_int("123") == 123
        assert safe_convert_to_int("-456") == -456
        assert safe_convert_to_int("0") == 0
        assert safe_convert_to_int("+789") == 789

    def test_valid_integers(self):
        """Test conversion of actual integer values"""
        assert safe_convert_to_int(123) == 123
        assert safe_convert_to_int(-456) == -456
        assert safe_convert_to_int(0) == 0

    def test_float_conversion(self):
        """Test conversion of float values (should truncate)"""
        assert safe_convert_to_int(123.45) == 123
        assert safe_convert_to_int(-78.9) == -78
        assert safe_convert_to_int(0.0) == 0

    def test_float_strings(self):
        """Test conversion of float strings (should truncate)"""
        assert safe_convert_to_int("123.99") == 123
        assert safe_convert_to_int("-45.67") == -45
        assert safe_convert_to_int("0.0") == 0

    def test_boolean_values(self):
        """Test conversion of boolean values"""
        assert safe_convert_to_int(True) == 1
        assert safe_convert_to_int(False) == 0

    def test_none_value(self):
        """Test conversion of None value"""
        assert safe_convert_to_int(None) == 0

    def test_invalid_strings(self):
        """Test conversion of invalid string values"""
        assert safe_convert_to_int("abc") == 0
        assert safe_convert_to_int("123abc") == 0
        assert safe_convert_to_int("") == 0
        assert safe_convert_to_int("   ") == 0

    def test_complex_numbers(self):
        """Test conversion of complex numbers"""
        assert safe_convert_to_int(3 + 4j) == 0

    def test_list_and_dict(self):
        """Test conversion of list and dictionary types"""
        assert safe_convert_to_int([1, 2, 3]) == 0
        assert safe_convert_to_int({"key": "value"}) == 0

    def test_whitespace_strings(self):
        """Test conversion of strings with whitespace"""
        assert safe_convert_to_int("  123  ") == 123
        assert safe_convert_to_int("  -456  ") == -456
        assert safe_convert_to_int("  abc  ") == 0

    def test_scientific_notation(self):
        """Test conversion of scientific notation strings"""
        assert safe_convert_to_int("1e3") == 1000
        assert safe_convert_to_int("1.5e2") == 150
        assert safe_convert_to_int("invalid_e") == 0

    def test_hexadecimal_strings(self):
        """Test conversion of hexadecimal strings"""
        # Hexadecimal strings are not directly convertible by int() without base
        assert safe_convert_to_int("0xFF") == 0
        assert safe_convert_to_int("FF") == 0

    def test_octal_strings(self):
        """Test conversion of octal strings"""
        # Octal strings are not directly convertible by int() without base
        assert safe_convert_to_int("0o77") == 0
        assert safe_convert_to_int("077") == 77  # This will work as decimal

    def test_binary_strings(self):
        """Test conversion of binary strings"""
        # Binary strings are not directly convertible by int() without base
        assert safe_convert_to_int("0b1010") == 0
        assert safe_convert_to_int("1010") == 1010  # This will work as decimal

    def test_very_large_numbers(self):
        """Test conversion of very large numbers"""
        large_num = 10**100
        assert safe_convert_to_int(large_num) == large_num

        # Very large float that can be converted to int
        assert safe_convert_to_int(1.0e100) == 10**100

    def test_numeric_string_with_commas(self):
        """Test conversion of numeric strings with commas"""
        assert safe_convert_to_int("1,000") == 0  # Commas make it invalid
        assert safe_convert_to_int("1,000,000") == 0

    def test_unicode_numeric_strings(self):
        """Test conversion of unicode numeric strings"""
        assert safe_convert_to_int("١٢٣") == 0  # Arabic numerals
        assert safe_convert_to_int("１２３") == 0  # Full-width numerals

    def test_special_numeric_values(self):
        """Test conversion of special numeric values"""
        assert safe_convert_to_int(math.inf) == 0
        assert safe_convert_to_int(-math.inf) == 0
        assert safe_convert_to_int(math.nan) == 0

    def test_string_with_newlines(self):
        """Test conversion of strings containing newlines"""
        assert safe_convert_to_int("123\n") == 123
        assert safe_convert_to_int("\n456") == 456
        assert safe_convert_to_int("abc\n") == 0

    def test_capturing_warning_output(self, capsys):
        """Test that warning messages are printed for invalid conversions"""
        # Test invalid string
        result = safe_convert_to_int("invalid")
        captured = capsys.readouterr()
        assert "Warning: Could not convert 'invalid' to int." in captured.out
        assert result == 0
        # Test None value
        result = safe_convert_to_int(None)
        captured = capsys.readouterr()
        assert "Warning: Could not convert 'None' to int." in captured.out
        assert result == 0

    def test_edge_case_strings(self):
        """Test various edge case strings"""
        # Boundary values
        assert (
            safe_convert_to_int(str(2**31 - 1)) == 2147483647
        )  # Max 32-bit signed int
        assert (
            safe_convert_to_int(str(-(2**31))) == -2147483648
        )  # Min 32-bit signed int

        # Strings that look like numbers but have issues
        assert safe_convert_to_int("123.") == 123
        assert safe_convert_to_int(".456") == 0
        assert safe_convert_to_int("123.456.789") == 0
