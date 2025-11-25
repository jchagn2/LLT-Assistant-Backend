# from advanced_functions import parse_nested_json, DataProcessingError
import json

import pytest

from data.raw.simple.simple3 import DataProcessingError, parse_nested_json


class TestParseNestedJson:
    """测试 parse_nested_json 函数的各种场景"""

    def test_basic_nested_json(self):
        """测试基本嵌套JSON解析"""
        # 输入包含嵌套JSON字符串的JSON
        input_json = '{"a": 1, "b": "{\\"c\\": 2, \\"d\\": \\"hello\\"}"}'

        result = parse_nested_json(input_json)

        expected = {"a": 1, "b": {"c": 2, "d": "hello"}}
        assert result == expected

    def test_deeply_nested_json(self):
        """测试深度嵌套JSON解析"""
        input_json = '{"level1": "{\\"level2\\": \\"{\\\\\\"level3\\\\\\": 123}\\"}"}'

        result = parse_nested_json(input_json)

        expected = {"level1": {"level2": {"level3": 123}}}
        assert result == expected

    def test_multiple_nested_fields(self):
        """测试多个嵌套字段"""
        input_json = '{"a": "{\\"x\\": 1}", "b": "{\\"y\\": 2}", "c": "normal string"}'

        result = parse_nested_json(input_json)

        expected = {"a": {"x": 1}, "b": {"y": 2}, "c": "normal string"}
        assert result == expected

    def test_nested_json_in_array(self):
        """测试数组中的嵌套JSON"""
        input_json = '{"items": ["{\\"name\\": \\"item1\\"}", "{\\"name\\": \\"item2\\"}", "plain text"]}'

        result = parse_nested_json(input_json)

        expected = {"items": [{"name": "item1"}, {"name": "item2"}, "plain text"]}
        assert result == expected

    def test_nested_array_in_json(self):
        """测试嵌套数组的解析"""
        input_json = '{"data": "{\\"numbers\\": [1, 2, 3], \\"nested\\": \\"{\\\\\\"array\\\\\\": [\\\\\\"a\\\\\\", \\\\\\"b\\\\\\"]}\\"}"}'

        result = parse_nested_json(input_json)

        expected = {"data": {"numbers": [1, 2, 3], "nested": {"array": ["a", "b"]}}}
        assert result == expected

    def test_mixed_nested_and_plain_strings(self):
        """测试混合嵌套JSON和普通字符串"""
        input_json = '{"json_field": "{\\"key\\": \\"value\\"}", "plain_field": "just a string", "number_field": 42}'

        result = parse_nested_json(input_json)

        expected = {
            "json_field": {"key": "value"},
            "plain_field": "just a string",
            "number_field": 42,
        }
        assert result == expected

    def test_no_nested_json(self):
        """测试没有嵌套JSON的普通JSON"""
        input_json = '{"name": "John", "age": 30, "active": true}'

        result = parse_nested_json(input_json)

        expected = {"name": "John", "age": 30, "active": True}
        assert result == expected

    def test_empty_json_object(self):
        """测试空JSON对象"""
        input_json = "{}"

        result = parse_nested_json(input_json)

        assert result == {}

    def test_json_with_null_values(self):
        """测试包含null值的JSON"""
        input_json = '{"field1": null, "field2": "{\\"nested\\": null}"}'

        result = parse_nested_json(input_json)

        expected = {"field1": None, "field2": {"nested": None}}
        assert result == expected

    def test_json_with_boolean_values(self):
        """测试包含布尔值的嵌套JSON"""
        input_json = '{"settings": "{\\"enabled\\": true, \\"admin\\": false}"}'

        result = parse_nested_json(input_json)

        expected = {"settings": {"enabled": True, "admin": False}}
        assert result == expected

    def test_json_with_float_numbers(self):
        """测试包含浮点数的嵌套JSON"""
        input_json = '{"metrics": "{\\"temperature\\": 23.5, \\"humidity\\": 65.2}"}'

        result = parse_nested_json(input_json)

        expected = {"metrics": {"temperature": 23.5, "humidity": 65.2}}
        assert result == expected

    def test_invalid_outer_json(self):
        """测试无效的外部JSON字符串"""
        input_json = '{"invalid: json}'

        with pytest.raises(DataProcessingError) as exc_info:
            parse_nested_json(input_json)

        assert "Invalid JSON string" in str(exc_info.value)

    def test_invalid_nested_json(self):
        """测试有效的JSON但包含无效的嵌套JSON字符串"""
        input_json = '{"valid": "json", "nested": "invalid { json" }'

        result = parse_nested_json(input_json)

        # 无效的嵌套JSON应该保持为字符串
        expected = {"valid": "json", "nested": "invalid { json"}
        assert result == expected

    def test_escape_sequences_in_strings(self):
        """测试包含转义序列的字符串"""
        input_json = '{"text": "Line 1\\\\nLine 2", "nested": "{\\"message\\": \\"Hello\\\\nWorld\\"}"}'

        result = parse_nested_json(input_json)

        expected = {"text": "Line 1\\nLine 2", "nested": {"message": "Hello\\nWorld"}}
        assert result == expected

    def test_special_characters_in_keys_and_values(self):
        """测试特殊字符在键和值中"""
        input_json = '{"key-with-dash": "value with spaces", "nested": "{\\"special.key\\": \\"value/with/slashes\\"}"}'

        result = parse_nested_json(input_json)

        expected = {
            "key-with-dash": "value with spaces",
            "nested": {"special.key": "value/with/slashes"},
        }
        assert result == expected

    def test_unicode_characters(self):
        """测试Unicode字符"""
        input_json = (
            '{"message": "Hello 世界", "nested": "{\\"greeting\\": \\"こんにちは\\"}"}'
        )

        result = parse_nested_json(input_json)

        expected = {"message": "Hello 世界", "nested": {"greeting": "こんにちは"}}
        assert result == expected

    def test_empty_string_input(self):
        """测试空字符串输入"""
        input_json = ""

        with pytest.raises(DataProcessingError) as exc_info:
            parse_nested_json(input_json)

        assert "Invalid JSON string" in str(exc_info.value)

    def test_whitespace_only_input(self):
        """测试只有空白的输入"""
        input_json = "   "

        with pytest.raises(DataProcessingError) as exc_info:
            parse_nested_json(input_json)

        assert "Invalid JSON string" in str(exc_info.value)

    def test_none_input(self):
        """测试None输入"""
        with pytest.raises(TypeError):
            parse_nested_json(None)

    def test_complex_real_world_scenario(self):
        """测试复杂的真实世界场景"""
        input_json = """
        {
            "user": "{\\"id\\": 123, \\"profile\\": \\"{\\\\\\"name\\\\\\": \\\\\\"John\\\\\\", \\\\\\"settings\\\\\\": \\\\\\"{\\\\\\\\\\\\\\"theme\\\\\\\\\\\\\\": \\\\\\\\\\\\\\"dark\\\\\\\\\\\\\\"}\\\\\\\"}\\"}",
            "metadata": "{\\"timestamp\\": \\"2023-01-01\\", \\"tags\\": [\\"important\\", \\"test\\"]}",
            "status": "active"
        }
        """

        result = parse_nested_json(input_json)

        expected = {
            "user": {
                "id": 123,
                "profile": {"name": "John", "settings": {"theme": "dark"}},
            },
            "metadata": {"timestamp": "2023-01-01", "tags": ["important", "test"]},
            "status": "active",
        }
        assert result == expected

    def test_preserves_original_structure(self):
        """测试保留原始结构"""
        input_json = '{"array": [1, "{\\"nested\\": 2}", 3], "object": {"inner": "{\\"deep\\": 4}"}}'

        result = parse_nested_json
