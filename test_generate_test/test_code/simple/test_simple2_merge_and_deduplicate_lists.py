# from complex_functions import merge_and_deduplicate_lists
import pytest

from data.raw.simple.simple2 import merge_and_deduplicate_lists


class TestMergeAndDeduplicateLists:
    """Test cases for merge_and_deduplicate_lists function"""

    def test_basic_merge_with_duplicates(self):
        """Test basic merging with duplicate elements"""
        list1 = [1, 2, 3, 4]
        list2 = [3, 4, 5, 6]
        result = merge_and_deduplicate_lists(list1, list2)
        expected = [1, 2, 3, 4, 5, 6]
        assert result == expected
        # Verify order is preserved (first occurrence)
        assert result.index(3) == 2  # 3 first appears at index 2 from list1
        assert result.index(4) == 3  # 4 first appears at index 3 from list1

    def test_empty_lists(self):
        """Test merging empty lists"""
        # Both lists empty
        result = merge_and_deduplicate_lists([], [])
        assert result == []

        # First list empty
        result = merge_and_deduplicate_lists([], [1, 2, 3])
        assert result == [1, 2, 3]

        # Second list empty
        result = merge_and_deduplicate_lists([1, 2, 3], [])
        assert result == [1, 2, 3]

    def test_no_duplicates(self):
        """Test merging lists with no duplicates"""
        list1 = [1, 2, 3]
        list2 = [4, 5, 6]
        result = merge_and_deduplicate_lists(list1, list2)
        assert result == [1, 2, 3, 4, 5, 6]

    def test_all_duplicates(self):
        """Test merging lists with all elements duplicated"""
        list1 = [1, 2, 3]
        list2 = [1, 2, 3]
        result = merge_and_deduplicate_lists(list1, list2)
        assert result == [1, 2, 3]
        assert len(result) == 3

    def test_preserve_order_first_occurrence(self):
        """Test that order is preserved based on first occurrence"""
        list1 = [1, 2, 3, 4]
        list2 = [4, 3, 2, 1]  # Reverse order with same elements
        result = merge_and_deduplicate_lists(list1, list2)
        # Should maintain order from first list
        assert result == [1, 2, 3, 4]

    def test_with_strings(self):
        """Test merging lists containing strings"""
        list1 = ["apple", "banana", "cherry"]
        list2 = ["banana", "date", "elderberry"]
        result = merge_and_deduplicate_lists(list1, list2)
        expected = ["apple", "banana", "cherry", "date", "elderberry"]
        assert result == expected

    def test_with_mixed_types(self):
        """Test merging lists with mixed data types"""
        list1 = [1, "hello", 3.14, True]
        list2 = ["hello", False, 1, None]
        result = merge_and_deduplicate_lists(list1, list2)
        expected = [1, "hello", 3.14, True, False, None]
        assert result == expected
        # Verify types are preserved
        assert isinstance(result[0], int)
        assert isinstance(result[1], str)
        assert isinstance(result[2], float)
        assert isinstance(result[3], bool)

    def test_with_none_values(self):
        """Test handling of None values"""
        list1 = [1, None, 3]
        list2 = [None, 4, 5]
        result = merge_and_deduplicate_lists(list1, list2)
        expected = [1, None, 3, 4, 5]
        assert result == expected

    def test_with_duplicate_none(self):
        """Test handling of multiple None values"""
        list1 = [None, 1, None]
        list2 = [2, None, 3]
        result = merge_and_deduplicate_lists(list1, list2)
        expected = [None, 1, 2, 3]
        assert result == expected
        # Should only have one None
        assert result.count(None) == 1

    def test_large_lists(self):
        """Test with larger lists to ensure performance and correctness"""
        list1 = list(range(1000))
        list2 = list(range(500, 1500))  # Overlapping range
        result = merge_and_deduplicate_lists(list1, list2)

        # Should contain all unique elements from both lists
        assert len(result) == 1500
        assert set(result) == set(range(1500))
        # Should preserve order (first occurrence)
        assert result[:1000] == list(range(1000))

    def test_with_custom_objects(self):
        """Test with custom objects (if they are hashable)"""

        class SimpleObject:
            def __init__(self, value):
                self.value = value

            def __eq__(self, other):
                return isinstance(other, SimpleObject) and self.value == other.value

            def __hash__(self):
                return hash(self.value)

        obj1 = SimpleObject(1)
        obj2 = SimpleObject(2)
        obj3 = SimpleObject(1)  # Duplicate of obj1

        list1 = [obj1, obj2]
        list2 = [obj3, SimpleObject(3)]

        result = merge_and_deduplicate_lists(list1, list2)
        assert len(result) == 3
        assert obj1 in result
        assert obj2 in result
        assert SimpleObject(3) in result

    def test_original_lists_unchanged(self):
        """Test that original lists are not modified"""
        list1 = [1, 2, 3]
        list2 = [3, 4, 5]
        list1_original = list1.copy()
        list2_original = list2.copy()

        result = merge_and_deduplicate_lists(list1, list2)

        # Original lists should remain unchanged
        assert list1 == list1_original
        assert list2 == list2_original
        # Result should be a new list
        assert result is not list1
        assert result is not list2

    def test_with_boolean_values(self):
        """Test handling of boolean values"""
        list1 = [True, False, True]
        list2 = [False, True, None]
        result = merge_and_deduplicate_lists(list1, list2)
        expected = [True, False, None]
        assert result == expected

    def test_with_floats(self):
        """Test handling of float values"""
        list1 = [1.1, 2.2, 3.3]
        list2 = [2.2, 3.3, 4.4]
        result = merge_and_deduplicate_lists(list1, list2)
        expected = [1.1, 2.2, 3.3, 4.4]
        assert result == expected

    def test_order_preservation_complex_case(self):
        """Test complex case for order preservation"""
        list1 = [1, 2, 3, 4, 5]
        list2 = [3, 1, 6, 7, 2]  # Mixed order with some duplicates
        result = merge_and_deduplicate_lists(list1, list2)
        # Elements from list1 should appear in their original order
        # New elements from list2 should appear in their relative order
        expected = [1, 2, 3, 4, 5, 6, 7]
        assert result == expected
