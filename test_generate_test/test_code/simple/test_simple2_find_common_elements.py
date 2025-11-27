# from complex_functions import find_common_elements
import pytest

from data.raw.simple.simple2 import find_common_elements


class TestFindCommonElements:
    """Test cases for find_common_elements function"""

    def test_basic_common_elements(self):
        """Test basic case with common elements"""
        lists = [[1, 2, 3], [2, 3, 4], [3, 4, 5]]
        result = find_common_elements(lists)
        assert result == [3]
        assert isinstance(result, list)

    def test_multiple_common_elements(self):
        """Test case with multiple common elements"""
        lists = [[1, 2, 3, 4], [2, 3, 4, 5], [3, 4, 5, 6]]
        result = find_common_elements(lists)
        assert sorted(result) == [3, 4]

    def test_no_common_elements(self):
        """Test case with no common elements"""
        lists = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
        result = find_common_elements(lists)
        assert result == []

    def test_empty_input_list(self):
        """Test case with empty input list"""
        result = find_common_elements([])
        assert result == []

    def test_single_list(self):
        """Test case with only one list"""
        lists = [[1, 2, 3, 4, 5]]
        result = find_common_elements(lists)
        assert sorted(result) == [1, 2, 3, 4, 5]

    def test_empty_inner_lists(self):
        """Test case with empty inner lists"""
        lists = [[], [1, 2], []]
        result = find_common_elements(lists)
        assert result == []

    def test_all_empty_lists(self):
        """Test case where all lists are empty"""
        lists = [[], [], []]
        result = find_common_elements(lists)
        assert result == []

    def test_duplicate_elements_within_lists(self):
        """Test case with duplicate elements within individual lists"""
        lists = [[1, 1, 2, 2], [1, 2, 2, 3], [1, 1, 1, 2]]
        result = find_common_elements(lists)
        assert sorted(result) == [1, 2]

    def test_string_elements(self):
        """Test case with string elements"""
        lists = [["a", "b", "c"], ["b", "c", "d"], ["c", "d", "e"]]
        result = find_common_elements(lists)
        assert result == ["c"]

    def test_mixed_data_types(self):
        """Test case with mixed data types"""
        lists = [[1, "a", True], [1, "a", False], [1, "a", None]]
        result = find_common_elements(lists)
        assert sorted(result) == [1, "a"]

    def test_large_number_of_lists(self):
        """Test case with large number of lists"""
        lists = [[1, 2, 3] for _ in range(100)]
        result = find_common_elements(lists)
        assert sorted(result) == [1, 2, 3]

    def test_none_values(self):
        """Test case with None values"""
        lists = [[None, 1, 2], [None, 2, 3], [None, 3, 4]]
        result = find_common_elements(lists)
        assert result == [None]

    def test_boolean_values(self):
        """Test case with boolean values"""
        lists = [[True, False, 1], [True, False, 2], [True, False, 3]]
        result = find_common_elements(lists)
        assert sorted(result) == [False, True]

    def test_floating_point_numbers(self):
        """Test case with floating point numbers"""
        lists = [[1.1, 2.2, 3.3], [2.2, 3.3, 4.4], [3.3, 4.4, 5.5]]
        result = find_common_elements(lists)
        assert result == [3.3]

    def test_early_termination(self):
        """Test that function terminates early when no common elements remain"""
        lists = [[1, 2, 3], [4, 5, 6], [7, 8, 9], [10, 11, 12]]
        result = find_common_elements(lists)
        assert result == []

    def test_preserve_order_from_first_list(self):
        """Test that order is preserved from the first list"""
        lists = [[3, 1, 2], [2, 1, 3], [1, 3, 2]]
        result = find_common_elements(lists)
        assert result == [3, 1, 2]  # Order should match first list

    def test_complex_nested_objects(self):
        """Test case with complex objects (though not recommended for common elements)"""
        obj1 = {"key": "value"}
        obj2 = {"key": "value"}
        lists = [[obj1], [obj2]]
        result = find_common_elements(lists)
        # Different objects with same content are not considered equal
        assert result == []

    def test_with_sets(self):
        """Test case where inner lists are actually sets (different object types)"""
        lists = [{1, 2, 3}, {2, 3, 4}, {3, 4, 5}]
        # This will work because sets are iterable
        result = find_common_elements(lists)
        assert result == [3]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
