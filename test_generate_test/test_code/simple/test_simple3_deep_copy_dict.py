import json
from datetime import datetime
from typing import Any, Dict, List

import pytest

from data.raw.simple.simple3 import DataProcessingError, deep_copy_dict

# from advanced_functions import DataProcessingError, deep_copy_dict


class TestDeepCopyDict:
    """Test cases for the deep_copy_dict function"""

    def test_basic_dict_copy(self):
        """Test copying a basic dictionary"""
        original = {"a": 1, "b": 2, "c": 3}
        copied = deep_copy_dict(original)

        # Verify the copy has same content
        assert copied == original
        # Verify it's a different object
        assert copied is not original
        # Verify modifying copy doesn't affect original
        copied["a"] = 100
        assert original["a"] == 1

    def test_nested_dict_copy(self):
        """Test copying nested dictionaries"""
        original = {
            "level1": {"level2": {"level3": "deep_value"}, "list_data": [1, 2, 3]},
            "simple_key": "simple_value",
        }
        copied = deep_copy_dict(original)

        # Verify nested structure is preserved
        assert copied["level1"]["level2"]["level3"] == "deep_value"
        # Verify it's a deep copy (nested objects are different)
        assert copied["level1"] is not original["level1"]
        assert copied["level1"]["level2"] is not original["level1"]["level2"]
        # Verify modifying nested copy doesn't affect original
        copied["level1"]["level2"]["level3"] = "modified"
        assert original["level1"]["level2"]["level3"] == "deep_value"

    def test_list_containing_dicts(self):
        """Test copying lists containing dictionaries"""
        original = [
            {"id": 1, "name": "Alice"},
            {"id": 2, "name": "Bob"},
            [{"nested": "dict"}],
        ]
        copied = deep_copy_dict(original)

        # Verify list structure is preserved
        assert len(copied) == len(original)
        # Verify dictionaries in list are copied (not same objects)
        assert copied[0] is not original[0]
        assert copied[0] == original[0]
        # Verify nested list with dict is properly copied
        assert copied[2][0] is not original[2][0]

    def test_complex_data_types(self):
        """Test copying with various data types"""
        original = {
            "string": "hello world",
            "integer": 42,
            "float": 3.14159,
            "boolean": True,
            "none": None,
            "list": [1, "two", 3.0],
            "tuple": (1, 2, 3),  # tuples become lists after JSON round-trip
            "empty_dict": {},
            "empty_list": [],
        }
        copied = deep_copy_dict(original)

        # Verify all data types are properly copied
        assert copied == original
        # Note: tuples become lists due to JSON serialization
        assert isinstance(copied["tuple"], list)

    def test_empty_dict(self):
        """Test copying an empty dictionary"""
        original = {}
        copied = deep_copy_dict(original)

        assert copied == original
        assert copied is not original
        assert len(copied) == 0

    def test_dict_with_special_json_values(self):
        """Test copying dictionaries with JSON-special values"""
        original = {
            "special_chars": "line\nbreak\ttab",
            "unicode": "中文 Español Français",
            "escape_chars": "quotes: \"double\" and 'single'",
            "math_symbols": "π ≈ 3.14 ± 0.01",
        }
        copied = deep_copy_dict(original)

        assert copied == original
        # Verify special characters are preserved
        assert "\n" in copied["special_chars"]
        assert "\t" in copied["special_chars"]

    def test_large_dict_performance(self):
        """Test copying a large dictionary (basic performance check)"""
        original = {f"key_{i}": f"value_{i}" for i in range(1000)}
        copied = deep_copy_dict(original)

        assert len(copied) == 1000
        assert copied == original
        assert copied is not original

    def test_circular_reference_error(self):
        """Test that circular references raise appropriate error"""
        original = {"a": 1}
        original["self"] = original  # Create circular reference

        with pytest.raises(DataProcessingError) as exc_info:
            deep_copy_dict(original)

        assert "Cannot deep copy object" in str(exc_info.value)
        # JSON can't serialize circular references, so this should fail

    def test_non_serializable_object_error(self):
        """Test error handling for non-serializable objects"""

        class CustomClass:
            def __init__(self, value):
                self.value = value

        original = {"custom_obj": CustomClass(42)}

        with pytest.raises(DataProcessingError) as exc_info:
            deep_copy_dict(original)

        assert "Cannot deep copy object" in str(exc_info.value)

    def test_function_object_error(self):
        """Test error handling for function objects (not JSON serializable)"""

        def sample_function():
            return "test"

        original = {"func": sample_function}

        with pytest.raises(DataProcessingError) as exc_info:
            deep_copy_dict(original)

        assert "Cannot deep copy object" in str(exc_info.value)

    def test_datetime_object_error(self):
        """Test error handling for datetime objects (without custom serializer)"""

        original = {"timestamp": datetime.now()}

        with pytest.raises(DataProcessingError) as exc_info:
            deep_copy_dict(original)

        assert "Cannot deep copy object" in str(exc_info.value)

    def test_none_input(self):
        """Test copying None input"""
        copied = deep_copy_dict(None)
        assert copied is None

    def test_non_dict_input(self):
        """Test copying non-dictionary inputs that are JSON serializable"""
        # Test with list
        original_list = [1, 2, 3, {"a": 1}]
        copied_list = deep_copy_dict(original_list)
        assert copied_list == original_list
        assert copied_list is not original_list
        assert copied_list[3] is not original_list[3]

        # Test with string
        original_str = "hello world"
        copied_str = deep_copy_dict(original_str)
        assert copied_str == original_str

        # Test with number
        original_num = 42
        copied_num = deep_copy_dict(original_num)
        assert copied_num == original_num

    def test_preservation_of_order(self):
        """Test that dictionary order is preserved (Python 3.7+ maintains insertion order)"""
        original = {"z": 1, "a": 2, "m": 3}
        copied = deep_copy_dict(original)

        # Verify order is preserved
        assert list(copied.keys()) == list(original.keys())
        assert list(copied.items()) == list(original.items())

    def test_multiple_nested_levels(self):
        """Test copying with multiple levels of nesting"""
        original = {"a": {"b": {"c": {"d": {"e": "final_value"}}}}}
        copied = deep_copy_dict(original)

        # Verify deep nesting is properly copied
        assert copied["a"]["b"]["c"]["d"]["e"] == "final_value"
        # Verify all levels are different objects
        assert copied["a"] is not original["a"]
        assert copied["a"]["b"] is not original["a"]["b"]
        assert copied["a"]["b"]["c"] is not original["a"]["b"]["c"]

    def test_mixed_nested_structures(self):
        """Test copying complex mixed nested structures"""
        original = {
            "users": [
                {
                    "id": 1,
                    "profile": {
                        "name": "Alice",
                        "settings": {"theme": "dark", "notifications": True},
                    },
                },
                {
                    "id": 2,
                    "profile": {
                        "name": "Bob",
                        "settings": {"theme": "light", "notifications": False},
                    },
                },
            ],
            "metadata": {"count": 2, "timestamp": "2023-01-01"},
        }
        copied = deep_copy_dict(original)

        # Verify complex structure is preserved
        assert copied["users"][0]["profile"]["settings"]["theme"] == "dark"
        # Verify all nested objects are different
        assert copied["users"][0] is not original["users"][0]
        assert copied["users"][0]["profile"] is not original["users"][0]["profile"]
