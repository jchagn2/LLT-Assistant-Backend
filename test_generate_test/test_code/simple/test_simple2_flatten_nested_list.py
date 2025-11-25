# from complex_functions import flatten_nested_list
import pytest

from data.raw.simple.simple2 import flatten_nested_list


class TestFlattenNestedList:
    """针对 flatten_nested_list 函数的单元测试类"""

    def test_flatten_flat_list(self):
        """测试扁平列表（无嵌套）"""
        # Arrange
        input_list = [1, 2, 3, 4, 5]

        # Act
        result = flatten_nested_list(input_list)

        # Assert
        assert result == [1, 2, 3, 4, 5]
        assert len(result) == 5

    def test_flatten_simple_nested_list(self):
        """测试简单嵌套列表"""
        # Arrange
        input_list = [1, [2, 3], 4, [5, 6]]

        # Act
        result = flatten_nested_list(input_list)

        # Assert
        assert result == [1, 2, 3, 4, 5, 6]
        assert len(result) == 6

    def test_flatten_deeply_nested_list(self):
        """测试深度嵌套列表"""
        # Arrange
        input_list = [1, [2, [3, [4, 5]]], 6, [7, [8]]]

        # Act
        result = flatten_nested_list(input_list)

        # Assert
        assert result == [1, 2, 3, 4, 5, 6, 7, 8]
        assert len(result) == 8

    def test_flatten_empty_list(self):
        """测试空列表"""
        # Arrange
        input_list = []

        # Act
        result = flatten_nested_list(input_list)

        # Assert
        assert result == []
        assert len(result) == 0

    def test_flatten_nested_empty_lists(self):
        """测试包含空嵌套列表的情况"""
        # Arrange
        input_list = [1, [], [2, []], 3, [[]]]

        # Act
        result = flatten_nested_list(input_list)

        # Assert
        assert result == [1, 2, 3]
        assert len(result) == 3

    def test_flatten_mixed_data_types(self):
        """测试混合数据类型"""
        # Arrange
        input_list = [1, "hello", [2.5, True], [None, [False, "world"]]]

        # Act
        result = flatten_nested_list(input_list)

        # Assert
        assert result == [1, "hello", 2.5, True, None, False, "world"]
        assert len(result) == 7

    def test_flatten_single_nested_list(self):
        """测试单个嵌套列表"""
        # Arrange
        input_list = [[1, 2, 3]]

        # Act
        result = flatten_nested_list(input_list)

        # Assert
        assert result == [1, 2, 3]
        assert len(result) == 3

    def test_flatten_complex_structure(self):
        """测试复杂嵌套结构"""
        # Arrange
        input_list = [[1, [2, [3]]], [[4, 5], 6], [7, [8, [9, [10]]]]]

        # Act
        result = flatten_nested_list(input_list)

        # Assert
        assert result == [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        assert len(result) == 10

    def test_flatten_preserves_order(self):
        """测试扁平化后保持原始顺序"""
        # Arrange
        input_list = [1, [2, 3], [4, [5, 6]], 7]

        # Act
        result = flatten_nested_list(input_list)

        # Assert
        assert result == [1, 2, 3, 4, 5, 6, 7]
        # 验证顺序正确
        for i, expected in enumerate([1, 2, 3, 4, 5, 6, 7]):
            assert result[i] == expected

    def test_flatten_with_objects(self):
        """测试包含自定义对象的情况"""

        # Arrange
        class SimpleObject:
            def __init__(self, value):
                self.value = value

            def __eq__(self, other):
                return isinstance(other, SimpleObject) and self.value == other.value

        obj1 = SimpleObject(1)
        obj2 = SimpleObject(2)
        input_list = [obj1, [obj2, [SimpleObject(3)]]]

        # Act
        result = flatten_nested_list(input_list)

        # Assert
        assert result == [obj1, obj2, SimpleObject(3)]
        assert len(result) == 3

    def test_flatten_already_flat(self):
        """测试已经是扁平列表的情况"""
        # Arrange
        input_list = ["a", "b", "c", "d"]

        # Act
        result = flatten_nested_list(input_list)

        # Assert
        assert result == ["a", "b", "c", "d"]
        assert result is not input_list  # 应该返回新列表

    def test_flatten_only_nested_lists(self):
        """测试只有嵌套列表的情况"""
        # Arrange
        input_list = [[[1]], [[2, 3]], [[[4]]]]

        # Act
        result = flatten_nested_list(input_list)

        # Assert
        assert result == [1, 2, 3, 4]
        assert len(result) == 4


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
