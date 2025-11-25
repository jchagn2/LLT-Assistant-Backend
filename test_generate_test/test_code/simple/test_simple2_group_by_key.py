# from complex_functions import group_by_key
import pytest

from data.raw.simple.simple2 import group_by_key


class TestGroupByKey:
    """Test cases for the group_by_key function"""

    def test_basic_grouping(self):
        """Test basic grouping functionality with string keys"""
        items = [
            {"name": "Alice", "department": "Engineering"},
            {"name": "Bob", "department": "Engineering"},
            {"name": "Charlie", "department": "Marketing"},
            {"name": "Diana", "department": "Engineering"},
        ]

        result = group_by_key(items, "department")

        expected = {
            "Engineering": [
                {"name": "Alice", "department": "Engineering"},
                {"name": "Bob", "department": "Engineering"},
                {"name": "Diana", "department": "Engineering"},
            ],
            "Marketing": [{"name": "Charlie", "department": "Marketing"}],
        }

        assert result == expected
        assert len(result["Engineering"]) == 3
        assert len(result["Marketing"]) == 1

    def test_numeric_keys(self):
        """Test grouping with numeric keys"""
        items = [
            {"id": 1, "category": 10},
            {"id": 2, "category": 20},
            {"id": 3, "category": 10},
            {"id": 4, "category": 30},
        ]

        result = group_by_key(items, "category")

        assert 10 in result
        assert 20 in result
        assert 30 in result
        assert len(result[10]) == 2
        assert len(result[20]) == 1
        assert len(result[30]) == 1

    def test_mixed_key_types(self):
        """Test grouping with mixed key types"""
        items = [
            {"id": 1, "group": "A"},
            {"id": 2, "group": 100},
            {"id": 3, "group": "A"},
            {"id": 4, "group": None},
        ]

        result = group_by_key(items, "group")

        assert "A" in result
        assert 100 in result
        assert None in result
        assert len(result["A"]) == 2
        assert len(result[100]) == 1
        assert len(result[None]) == 1

    def test_none_values_for_key(self):
        """Test handling of None values for the grouping key"""
        items = [
            {"name": "Alice", "team": None},
            {"name": "Bob", "team": "Red"},
            {"name": "Charlie", "team": None},
            {"name": "Diana"},  # Missing key entirely
        ]

        result = group_by_key(items, "team")

        assert None in result
        assert "Red" in result
        assert len(result[None]) == 3  # Two explicit None + one missing key
        assert len(result["Red"]) == 1

    def test_empty_list(self):
        """Test grouping with empty input list"""
        result = group_by_key([], "any_key")

        assert result == {}
        assert len(result) == 0

    def test_missing_key_in_all_items(self):
        """Test when the grouping key is missing from all items"""
        items = [{"name": "Alice", "age": 25}, {"name": "Bob", "age": 30}]

        result = group_by_key(items, "department")  # Key that doesn't exist

        assert None in result
        assert len(result) == 1
        assert len(result[None]) == 2

    def test_duplicate_items(self):
        """Test grouping with duplicate items"""
        item = {"id": 1, "type": "A"}
        items = [item, item, item]  # Same object repeated

        result = group_by_key(items, "type")

        assert "A" in result
        assert len(result["A"]) == 3
        # All items should be the same object reference
        assert result["A"][0] is result["A"][1]
        assert result["A"][1] is result["A"][2]

    def test_complex_nested_values(self):
        """Test grouping with complex nested values"""
        items = [
            {"key": "group1", "data": {"nested": {"value": 1}}},
            {"key": "group1", "data": {"nested": {"value": 2}}},
            {"key": "group2", "data": {"nested": {"value": 3}}},
        ]

        result = group_by_key(items, "key")

        assert "group1" in result
        assert "group2" in result
        assert len(result["group1"]) == 2
        assert len(result["group2"]) == 1
        assert result["group1"][0]["data"]["nested"]["value"] == 1
        assert result["group1"][1]["data"]["nested"]["value"] == 2

    def test_special_characters_in_keys(self):
        """Test grouping with special characters in key values"""
        items = [
            {"id": 1, "code": "A@B#C"},
            {"id": 2, "code": "A@B#C"},
            {"id": 3, "code": "D$E%F"},
        ]

        result = group_by_key(items, "code")

        assert "A@B#C" in result
        assert "D$E%F" in result
        assert len(result["A@B#C"]) == 2
        assert len(result["D$E%F"]) == 1

    def test_boolean_keys(self):
        """Test grouping with boolean keys"""
        items = [
            {"id": 1, "active": True},
            {"id": 2, "active": False},
            {"id": 3, "active": True},
            {"id": 4, "active": True},
        ]

        result = group_by_key(items, "active")

        assert True in result
        assert False in result
        assert len(result[True]) == 3
        assert len(result[False]) == 1

    def test_empty_string_key(self):
        """Test grouping with empty string as key value"""
        items = [
            {"id": 1, "tag": ""},
            {"id": 2, "tag": "important"},
            {"id": 3, "tag": ""},
        ]

        result = group_by_key(items, "tag")

        assert "" in result
        assert "important" in result
        assert len(result[""]) == 2
        assert len(result["important"]) == 1

    def test_large_number_of_groups(self):
        """Test grouping with a large number of distinct groups"""
        items = [{"id": i, "group": f"group_{i}"} for i in range(100)]

        result = group_by_key(items, "group")

        assert len(result) == 100
        for i in range(100):
            group_key = f"group_{i}"
            assert group_key in result
            assert len(result[group_key]) == 1
            assert result[group_key][0]["id"] == i

    def test_preservation_of_original_items(self):
        """Test that original items are preserved without modification"""
        original_item = {"id": 1, "category": "A", "data": [1, 2, 3]}
        items = [original_item.copy()]

        result = group_by_key(items, "category")

        # Verify the item in the result is equivalent but not necessarily the same object
        assert result["A"][0] == original_item
        # Verify the original item wasn't modified
        assert original_item == {"id": 1, "category": "A", "data": [1, 2, 3]}

    def test_none_as_grouping_key(self):
        """Test when None is passed as the grouping key parameter"""
        items = [{"id": 1}, {"id": 2}]

        result = group_by_key(items, None)

        assert None in result
        assert len(result[None]) == 2

    def test_dict_keys(self):
        """Test grouping with dictionary objects as keys (edge case)"""
        items = [
            {"id": 1, "config": {"key": "value"}},
            {"id": 2, "config": {"key": "value"}},  # Same dict content
            {"id": 3, "config": {"key": "different"}},
        ]

        result = group_by_key(items, "config")

        # Dictionary keys will be grouped by object identity, not content
        # This test documents this behavior
        assert len(result) == 3  # Each dict is a distinct object
        for key in result:
            assert len(result[key]) == 1
