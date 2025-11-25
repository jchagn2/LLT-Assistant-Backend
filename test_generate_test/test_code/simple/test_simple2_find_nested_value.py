# from complex_functions import find_nested_value
import pytest

from data.raw.simple.simple2 import find_nested_value


class TestFindNestedValue:
    """Test cases for find_nested_value function"""

    def test_valid_nested_structure(self):
        """Test finding value in valid nested dictionary structure"""
        data = {"level1": {"level2": {"level3": "target_value"}}}
        keys = ["level1", "level2", "level3"]
        result = find_nested_value(data, keys)
        assert result == "target_value"

    def test_single_level_dict(self):
        """Test finding value in single level dictionary"""
        data = {"key": "value"}
        keys = ["key"]
        result = find_nested_value(data, keys)
        assert result == "value"

    def test_middle_level_value(self):
        """Test finding value at middle level of nesting"""
        data = {"a": {"b": "middle_value", "c": {"d": "deep_value"}}}
        keys = ["a", "b"]
        result = find_nested_value(data, keys)
        assert result == "middle_value"

    def test_nonexistent_first_key(self):
        """Test when first key doesn't exist"""
        data = {"existing_key": {"nested": "value"}}
        keys = ["nonexistent_key", "nested"]
        result = find_nested_value(data, keys)
        assert result is None

    def test_nonexistent_middle_key(self):
        """Test when middle key doesn't exist"""
        data = {"level1": {"existing_key": "value"}}
        keys = ["level1", "nonexistent_key", "level3"]
        result = find_nested_value(data, keys)
        assert result is None

    def test_nonexistent_last_key(self):
        """Test when last key doesn't exist"""
        data = {"level1": {"level2": {}}}
        keys = ["level1", "level2", "nonexistent_key"]
        result = find_nested_value(data, keys)
        assert result is None

    def test_empty_keys_list(self):
        """Test with empty keys list - should return the entire data"""
        data = {"key": "value"}
        keys = []
        result = find_nested_value(data, keys)
        assert result == data

    def test_empty_dict_with_keys(self):
        """Test with empty dictionary but non-empty keys"""
        data = {}
        keys = ["key1", "key2"]
        result = find_nested_value(data, keys)
        assert result is None

    def test_none_data(self):
        """Test with None as data parameter"""
        data = None
        keys = ["key1", "key2"]
        result = find_nested_value(data, keys)
        assert result is None

    def test_numeric_keys(self):
        """Test with numeric keys in nested structure"""
        data = {"1": {"2": {"3": "numeric_value"}}}
        keys = ["1", "2", "3"]
        result = find_nested_value(data, keys)
        assert result == "numeric_value"

    def test_mixed_data_types(self):
        """Test with mixed data types in nested values"""
        data = {
            "level1": {
                "level2": {
                    "string": "text",
                    "number": 42,
                    "list": [1, 2, 3],
                    "dict": {"nested": "value"},
                    "none": None,
                    "boolean": True,
                }
            }
        }

        # Test string value
        result = find_nested_value(data, ["level1", "level2", "string"])
        assert result == "text"

        # Test number value
        result = find_nested_value(data, ["level1", "level2", "number"])
        assert result == 42

        # Test list value
        result = find_nested_value(data, ["level1", "level2", "list"])
        assert result == [1, 2, 3]

        # Test nested dict value
        result = find_nested_value(data, ["level1", "level2", "dict"])
        assert result == {"nested": "value"}

        # Test None value
        result = find_nested_value(data, ["level1", "level2", "none"])
        assert result is None

        # Test boolean value
        result = find_nested_value(data, ["level1", "level2", "boolean"])
        assert result is True

    def test_deep_nesting(self):
        """Test with very deep nesting"""
        data = {"a": {"b": {"c": {"d": {"e": {"f": {"g": "deep_value"}}}}}}}
        keys = ["a", "b", "c", "d", "e", "f", "g"]
        result = find_nested_value(data, keys)
        assert result == "deep_value"

    def test_duplicate_keys_different_levels(self):
        """Test when same key appears at different nesting levels"""
        data = {"key": {"key": "nested_value"}}
        # Should get the nested value, not the outer dict
        result = find_nested_value(data, ["key", "key"])
        assert result == "nested_value"

    def test_partial_match_followed_by_nonexistent(self):
        """Test when partial path exists but final key doesn't"""
        data = {"valid": {"path": {"exists": "value"}}}
        keys = ["valid", "path", "nonexistent"]
        result = find_nested_value(data, keys)
        assert result is None

    def test_keys_containing_special_characters(self):
        """Test with keys containing special characters"""
        data = {
            "key-with-dash": {"key_with_underscore": {"key.with.dots": "special_value"}}
        }
        keys = ["key-with-dash", "key_with_underscore", "key.with.dots"]
        result = find_nested_value(data, keys)
        assert result == "special_value"

    def test_large_nested_structure(self):
        """Test with large nested structure"""
        data = {}
        current = data
        keys = []

        # Create a large nested structure
        for i in range(100):
            key = f"level_{i}"
            current[key] = {}
            current = current[key]
            keys.append(key)

        # Add final value
        current["final"] = "target_value"
        keys.append("final")

        result = find_nested_value(data, keys)
        assert result == "target_value"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
