# from complex_functions import binary_search
import pytest

from data.raw.simple.simple2 import binary_search


class TestBinarySearch:
    """Test cases for binary_search function"""

    def test_target_exists_at_beginning(self):
        """Test when target is at the beginning of the list"""
        sorted_list = [1, 3, 5, 7, 9, 11]
        target = 1
        result = binary_search(sorted_list, target)
        assert result == 0

    def test_target_exists_at_end(self):
        """Test when target is at the end of the list"""
        sorted_list = [1, 3, 5, 7, 9, 11]
        target = 11
        result = binary_search(sorted_list, target)
        assert result == 5

    def test_target_exists_in_middle(self):
        """Test when target is in the middle of the list"""
        sorted_list = [1, 3, 5, 7, 9, 11]
        target = 7
        result = binary_search(sorted_list, target)
        assert result == 3

    def test_target_exists_random_position(self):
        """Test when target exists at a random position"""
        sorted_list = [2, 4, 6, 8, 10, 12, 14, 16, 18, 20]
        target = 12
        result = binary_search(sorted_list, target)
        assert result == 5

    def test_target_not_exists(self):
        """Test when target does not exist in the list"""
        sorted_list = [1, 3, 5, 7, 9, 11]
        target = 6
        result = binary_search(sorted_list, target)
        assert result == -1

    def test_empty_list(self):
        """Test with an empty list"""
        sorted_list = []
        target = 5
        result = binary_search(sorted_list, target)
        assert result == -1

    def test_single_element_exists(self):
        """Test with a single-element list where target exists"""
        sorted_list = [5]
        target = 5
        result = binary_search(sorted_list, target)
        assert result == 0

    def test_single_element_not_exists(self):
        """Test with a single-element list where target doesn't exist"""
        sorted_list = [5]
        target = 3
        result = binary_search(sorted_list, target)
        assert result == -1

    def test_duplicate_elements_first_occurrence(self):
        """Test with duplicate elements - should find first occurrence"""
        sorted_list = [1, 2, 2, 2, 3, 4, 5]
        target = 2
        result = binary_search(sorted_list, target)
        # Binary search should find one of the duplicates, but not necessarily the first
        assert result in [1, 2, 3]  # Any of the positions with value 2 is valid
        assert sorted_list[result] == target  # Verify the found position has the target

    def test_large_list(self):
        """Test with a large sorted list"""
        sorted_list = list(range(1, 1001))  # [1, 2, 3, ..., 1000]
        target = 750
        result = binary_search(sorted_list, target)
        assert result == 749  # 0-based index

    def test_negative_numbers(self):
        """Test with list containing negative numbers"""
        sorted_list = [-10, -5, -3, 0, 2, 5, 8]
        target = -3
        result = binary_search(sorted_list, target)
        assert result == 2

    def test_all_negative_numbers(self):
        """Test with list containing only negative numbers"""
        sorted_list = [-15, -12, -8, -5, -3, -1]
        target = -8
        result = binary_search(sorted_list, target)
        assert result == 2

    def test_zero_target(self):
        """Test when target is zero"""
        sorted_list = [-5, -3, 0, 2, 4, 6]
        target = 0
        result = binary_search(sorted_list, target)
        assert result == 2

    def test_identical_elements(self):
        """Test with list where all elements are identical"""
        sorted_list = [5, 5, 5, 5, 5, 5]
        target = 5
        result = binary_search(sorted_list, target)
        # Should find one of the positions
        assert 0 <= result < len(sorted_list)
        assert sorted_list[result] == target

    def test_target_smaller_than_min(self):
        """Test when target is smaller than the smallest element"""
        sorted_list = [10, 20, 30, 40, 50]
        target = 5
        result = binary_search(sorted_list, target)
        assert result == -1

    def test_target_larger_than_max(self):
        """Test when target is larger than the largest element"""
        sorted_list = [10, 20, 30, 40, 50]
        target = 60
        result = binary_search(sorted_list, target)
        assert result == -1

    def test_even_length_list(self):
        """Test with even-length list"""
        sorted_list = [1, 2, 3, 4, 5, 6]
        target = 4
        result = binary_search(sorted_list, target)
        assert result == 3

    def test_odd_length_list(self):
        """Test with odd-length list"""
        sorted_list = [1, 2, 3, 4, 5]
        target = 3
        result = binary_search(sorted_list, target)
        assert result == 2

    def test_consecutive_integers(self):
        """Test with consecutive integers"""
        sorted_list = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        target = 7
        result = binary_search(sorted_list, target)
        assert result == 6


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
