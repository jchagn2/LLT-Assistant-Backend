# from complex_functions import custom_sort
import pytest

from data.raw.simple.simple2 import custom_sort

# Looking at the `custom_sort` function, I'll generate comprehensive pytest tests that cover various scenarios including edge cases, error handling, and typical use cases.
# ```python


class TestCustomSort:
    """Test cases for custom_sort function"""

    def test_basic_mixed_types(self):
        """Test basic functionality with mixed integers and strings"""
        input_list = [3, "apple", 1, "banana", 2, "cherry"]
        expected = [
            1,
            2,
            3,
            "banana",
            "cherry",
            "apple",
        ]  # numbers ascending, strings by length descending
        result = custom_sort(input_list)
        assert result == expected

    def test_only_integers(self):
        """Test with list containing only integers"""
        input_list = [5, 2, 8, 1, 9]
        expected = [1, 2, 5, 8, 9]
        result = custom_sort(input_list)
        assert result == expected

    def test_only_strings(self):
        """Test with list containing only strings"""
        input_list = ["a", "abc", "ab", "abcd"]
        expected = ["abcd", "abc", "ab", "a"]  # sorted by length descending
        result = custom_sort(input_list)
        assert result == expected

    def test_empty_list(self):
        """Test with empty list"""
        input_list = []
        expected = []
        result = custom_sort(input_list)
        assert result == expected

    def test_single_element(self):
        """Test with single element lists"""
        # Single integer
        assert custom_sort([42]) == [42]

        # Single string
        assert custom_sort(["hello"]) == ["hello"]

    def test_duplicate_elements(self):
        """Test with duplicate elements"""
        input_list = [3, 2, 3, "apple", "banana", "apple", 2]
        expected = [
            2,
            2,
            3,
            3,
            "banana",
            "apple",
            "apple",
        ]  # duplicates preserved, strings by length
        result = custom_sort(input_list)
        assert result == expected

    def test_strings_same_length(self):
        """Test strings with same length - should maintain original order for same-length strings"""
        input_list = ["cat", "dog", "bat", 1, 2]
        expected = [
            1,
            2,
            "cat",
            "dog",
            "bat",
        ]  # strings with same length maintain relative order
        result = custom_sort(input_list)
        assert result == expected

    def test_large_numbers(self):
        """Test with large numbers"""
        input_list = [1000, 1, 999, "test"]
        expected = [1, 999, 1000, "test"]
        result = custom_sort(input_list)
        assert result == expected

    def test_negative_numbers(self):
        """Test with negative numbers"""
        input_list = [-5, 3, -1, 0, "text"]
        expected = [-5, -1, 0, 3, "text"]
        result = custom_sort(input_list)
        assert result == expected

    def test_mixed_with_other_types(self):
        """Test that non-integer/string types are handled"""
        input_list = [
            3,
            "hello",
            1.5,
            True,
            "world",
        ]  # 1.5 and True should be treated as integers
        # Note: The function only handles int and str, other types might cause issues
        # This test expects the function to handle mixed types gracefully
        result = custom_sort(input_list)
        # Integers should be sorted first, then strings by length
        assert isinstance(result[0], (int, float, bool))
        assert isinstance(result[-1], str)

    def test_very_long_strings(self):
        """Test with strings of varying lengths"""
        input_list = ["a", "very long string indeed", "medium", "short", 5, 1]
        expected = [1, 5, "very long string indeed", "medium", "short", "a"]
        result = custom_sort(input_list)
        assert result == expected

    def test_unicode_strings(self):
        """Test with unicode characters"""
        input_list = ["café", "hello", "世界", "a", 3, 1]
        expected = [1, 3, "hello", "café", "世界", "a"]
        result = custom_sort(input_list)
        assert result == expected

    def test_numbers_as_strings(self):
        """Test that numeric strings are treated as strings, not numbers"""
        input_list = ["10", "2", "100", 5, 1]
        expected = [1, 5, "100", "10", "2"]  # "100" is longest, then "10", then "2"
        result = custom_sort(input_list)
        assert result == expected

    def test_preservation_of_original(self):
        """Test that original list is not modified"""
        input_list = [3, "apple", 1, "banana"]
        original_copy = input_list.copy()
        result = custom_sort(input_list)
        assert input_list == original_copy  # Original should be unchanged
        assert result != input_list  # Result should be different (sorted)

    def test_complex_mixed_case(self):
        """Test a complex mixed case"""
        input_list = [15, "short", -3, "a very long string", 0, "medium length", 7, "z"]
        expected = [-3, 0, 7, 15, "a very long string", "medium length", "short", "z"]
        result = custom_sort(input_list)
        assert result == expected

    def test_all_same_length_strings(self):
        """Test when all strings have the same length"""
        input_list = ["cat", "dog", "bat", 3, 1, 2]
        expected = [
            1,
            2,
            3,
            "cat",
            "dog",
            "bat",
        ]  # Order of same-length strings preserved
        result = custom_sort(input_list)
        assert result == expected


# Edge cases and error handling tests
class TestCustomSortEdgeCases:
    """Edge cases and error handling for custom_sort function"""

    def test_none_values(self):
        """Test how function handles None values"""
        # The function doesn't explicitly handle None, so this tests its behavior
        input_list = [3, None, "test", 1]
        with pytest.raises(TypeError):
            # None cannot be compared with integers/strings in sorting
            custom_sort(input_list)

    def test_nested_lists(self):
        """Test with nested lists (should raise TypeError)"""
        input_list = [3, ["nested"], "string", 1]
        with pytest.raises(TypeError):
            # Lists cannot be compared with integers/strings
            custom_sort(input_list)

    def test_dict_in_list(self):
        """Test with dictionaries in list (should raise TypeError)"""
        input_list = [3, {"key": "value"}, "string", 1]
        with pytest.raises(TypeError):
            # Dicts cannot be compared with integers/strings
            custom_sort(input_list)

    def test_large_list_performance(self):
        """Test performance with large list (basic smoke test)"""
        large_list = list(range(1000)) + ["test"] * 100
        result = custom_sort(large_list)
        # Verify first elements are sorted numbers
        assert all(isinstance(x, int) for x in result[:1000])
        # Verify last elements are strings
        assert all(isinstance(x, str) for x in result[1000:])

    def test_very_large_strings(self):
        """Test with very large strings"""
        long_str = "a" * 1000
        medium_str = "b" * 500
        short_str = "c" * 10
        input_list = [5, 1, long_str, medium_str, short_str]
        expected = [1, 5, long_str, medium_str, short_str]
        result = custom_sort(input_list)
        assert result == expected
