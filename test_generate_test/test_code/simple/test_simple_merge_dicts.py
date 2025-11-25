# from math_functions import merge_dicts
import pytest

from data.raw.simple.simple import merge_dicts


class TestMergeDicts:
    """Test cases for the merge_dicts function."""

    def test_merge_empty_dicts(self):
        """Test merging two empty dictionaries."""
        dict1 = {}
        dict2 = {}
        result = merge_dicts(dict1, dict2)
        expected = {}
        assert result == expected
        assert result is not dict1  # Should return a new dict
        assert result is not dict2  # Should return a new dict

    def test_merge_first_dict_empty(self):
        """Test merging when first dictionary is empty."""
        dict1 = {}
        dict2 = {"a": 1, "b": 2}
        result = merge_dicts(dict1, dict2)
        expected = {"a": 1, "b": 2}
        assert result == expected

    def test_merge_second_dict_empty(self):
        """Test merging when second dictionary is empty."""
        dict1 = {"a": 1, "b": 2}
        dict2 = {}
        result = merge_dicts(dict1, dict2)
        expected = {"a": 1, "b": 2}
        assert result == expected

    def test_merge_no_overlapping_keys(self):
        """Test merging dictionaries with no overlapping keys."""
        dict1 = {"a": 1, "b": 2}
        dict2 = {"c": 3, "d": 4}
        result = merge_dicts(dict1, dict2)
        expected = {"a": 1, "b": 2, "c": 3, "d": 4}
        assert result == expected

    def test_merge_with_overlapping_keys(self):
        """Test merging dictionaries with overlapping keys - dict2 should override."""
        dict1 = {"a": 1, "b": 2, "c": 3}
        dict2 = {"b": 20, "c": 30, "d": 4}
        result = merge_dicts(dict1, dict2)
        expected = {"a": 1, "b": 20, "c": 30, "d": 4}
        assert result == expected

    def test_merge_with_none_values(self):
        """Test merging dictionaries containing None values."""
        dict1 = {"a": 1, "b": None}
        dict2 = {"b": 2, "c": None}
        result = merge_dicts(dict1, dict2)
        expected = {"a": 1, "b": 2, "c": None}
        assert result == expected

    def test_merge_with_false_values(self):
        """Test merging dictionaries containing False, 0, and empty string values."""
        dict1 = {"a": False, "b": 0, "c": ""}
        dict2 = {"b": 1, "d": "test"}
        result = merge_dicts(dict1, dict2)
        expected = {"a": False, "b": 1, "c": "", "d": "test"}
        assert result == expected

    def test_merge_with_complex_values(self):
        """Test merging dictionaries with complex values (lists, dicts, objects)."""
        dict1 = {"a": [1, 2, 3], "b": {"x": 1, "y": 2}}
        dict2 = {"b": {"x": 10, "z": 3}, "c": "hello"}
        result = merge_dicts(dict1, dict2)
        expected = {"a": [1, 2, 3], "b": {"x": 10, "z": 3}, "c": "hello"}
        assert result == expected

    def test_merge_preserves_original_dicts(self):
        """Test that original dictionaries are not modified."""
        dict1 = {"a": 1, "b": 2}
        dict2 = {"b": 20, "c": 3}
        dict1_original = dict1.copy()
        dict2_original = dict2.copy()

        result = merge_dicts(dict1, dict2)

        # Originals should remain unchanged
        assert dict1 == dict1_original
        assert dict2 == dict2_original
        # Result should be a new dictionary
        assert result is not dict1
        assert result is not dict2

    def test_merge_large_dicts(self):
        """Test merging large dictionaries."""
        dict1 = {str(i): i for i in range(100)}
        dict2 = {str(i): i * 2 for i in range(50, 150)}
        result = merge_dicts(dict1, dict2)

        # Verify all keys are present
        expected_keys = set(dict1.keys()) | set(dict2.keys())
        assert set(result.keys()) == expected_keys

        # Verify values are correctly overridden
        for key in dict1:
            if key in dict2:
                assert result[key] == dict2[key]  # dict2 overrides
            else:
                assert result[key] == dict1[key]

        for key in dict2:
            if key not in dict1:
                assert result[key] == dict2[key]

    def test_merge_with_special_keys(self):
        """Test merging with special dictionary keys."""
        dict1 = {"": "empty", None: "none_key", 123: "number_key"}
        dict2 = {"": "overridden", "new_key": "value"}
        result = merge_dicts(dict1, dict2)
        expected = {
            "": "overridden",
            None: "none_key",
            123: "number_key",
            "new_key": "value",
        }
        assert result == expected


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
