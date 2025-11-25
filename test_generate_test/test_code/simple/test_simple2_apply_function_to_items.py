# from functools import partial
# from complex_functions import apply_function_to_items
import pytest

from data.raw.simple.simple2 import apply_function_to_items


class TestApplyFunctionToItems:
    """Test cases for apply_function_to_items function"""

    def test_basic_function_application(self):
        """Test applying a simple function to a list of integers"""
        items = [1, 2, 3, 4, 5]
        func = lambda x: x * 2

        result = apply_function_to_items(items, func)

        assert result == [2, 4, 6, 8, 10]
        assert len(result) == len(items)

    def test_string_transformation(self):
        """Test applying string transformation functions"""
        items = ["hello", "world", "test"]
        func = lambda s: s.upper()

        result = apply_function_to_items(items, func)

        assert result == ["HELLO", "WORLD", "TEST"]
        assert all(isinstance(item, str) for item in result)

    def test_type_conversion_function(self):
        """Test applying type conversion functions"""
        items = ["1", "2", "3"]
        func = int

        result = apply_function_to_items(items, func)

        assert result == [1, 2, 3]
        assert all(isinstance(item, int) for item in result)

    def test_empty_list(self):
        """Test with empty input list"""
        items = []
        func = lambda x: x * 2

        result = apply_function_to_items(items, func)

        assert result == []
        assert len(result) == 0

    def test_none_values(self):
        """Test handling of None values in the list"""
        items = [1, None, 3, None, 5]
        func = lambda x: x if x is not None else 0

        result = apply_function_to_items(items, func)

        assert result == [1, 0, 3, 0, 5]

    def test_complex_objects(self):
        """Test with complex objects in the list"""
        items = [{"name": "Alice", "age": 25}, {"name": "Bob", "age": 30}]
        func = lambda person: f"{person['name']} is {person['age']} years old"

        result = apply_function_to_items(items, func)

        expected = ["Alice is 25 years old", "Bob is 30 years old"]
        assert result == expected

    def test_function_with_side_effects(self):
        """Test with a function that has side effects"""
        counter = {"count": 0}

        def counting_func(x):
            counter["count"] += 1
            return x * 2

        items = [1, 2, 3]
        result = apply_function_to_items(items, counting_func)

        assert result == [2, 4, 6]
        assert counter["count"] == 3  # Function should be called once per item

    def test_identity_function(self):
        """Test with identity function (returns input unchanged)"""
        items = [1, "hello", None, [1, 2, 3], {"key": "value"}]
        func = lambda x: x

        result = apply_function_to_items(items, func)

        assert result == items
        assert result is not items  # Should return a new list

    def test_function_raising_exceptions(self):
        """Test behavior when function raises exceptions for some items"""

        def risky_func(x):
            if x == 0:
                raise ValueError("Cannot process zero")
            return 10 / x

        items = [1, 2, 0, 4]

        # Should raise exception when function fails
        with pytest.raises(ValueError, match="Cannot process zero"):
            apply_function_to_items(items, risky_func)

    def test_preservation_of_order(self):
        """Test that the order of items is preserved"""
        items = [3, 1, 4, 1, 5, 9, 2, 6]
        func = lambda x: x * 10

        result = apply_function_to_items(items, func)

        # Order should be preserved
        assert result == [30, 10, 40, 10, 50, 90, 20, 60]

    def test_nested_lists(self):
        """Test with nested lists as items"""
        items = [[1, 2], [3, 4, 5], [6]]
        func = sum

        result = apply_function_to_items(items, func)

        assert result == [3, 12, 6]

    def test_function_returning_different_types(self):
        """Test with function that returns different types"""
        items = [1, "hello", 3.14]
        func = type

        result = apply_function_to_items(items, func)

        assert result == [int, str, float]

    @pytest.mark.parametrize(
        "items,func,expected",
        [
            # Test case 1: Square numbers
            ([1, 2, 3], lambda x: x**2, [1, 4, 9]),
            # Test case 2: String length
            (["a", "bb", "ccc"], len, [1, 2, 3]),
            # Test case 3: Boolean conversion
            ([0, 1, "", "text"], bool, [False, True, False, True]),
        ],
    )
    def test_parametrized_cases(self, items, func, expected):
        """Parameterized test for various scenarios"""
        result = apply_function_to_items(items, func)
        assert result == expected

    def test_large_list_performance(self):
        """Test with a large list to ensure reasonable performance"""
        items = list(range(1000))
        func = lambda x: x * 2

        result = apply_function_to_items(items, func)

        assert len(result) == 1000
        assert result[0] == 0
        assert result[999] == 1998
        assert result[500] == 1000

    def test_function_with_keyword_arguments(self):
        """Test with function that uses keyword arguments"""

        def multiplier(x, factor=2):
            return x * factor

        items = [1, 2, 3]

        # Test with default factor
        result1 = apply_function_to_items(items, multiplier)
        assert result1 == [2, 4, 6]
