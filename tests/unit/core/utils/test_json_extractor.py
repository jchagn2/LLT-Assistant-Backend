"""Unit tests for JSON extraction utilities."""

import pytest

from app.core.utils.json_extractor import (
    JSONExtractionError,
    extract_json_from_llm_response,
    safe_json_parse,
    validate_json_schema,
)


class TestExtractJsonFromLLMResponse:
    """Test cases for extract_json_from_llm_response function."""

    def test_direct_json_parsing_dict(self):
        """Test parsing pure JSON object directly."""
        response = '{"key": "value", "number": 42}'
        result = extract_json_from_llm_response(response)
        assert result == {"key": "value", "number": 42}

    def test_direct_json_parsing_list(self):
        """Test parsing pure JSON array directly."""
        response = '[{"key": "value"}, {"key": "value2"}]'
        result = extract_json_from_llm_response(response, expected_type=list)
        assert result == [{"key": "value"}, {"key": "value2"}]

    def test_json_with_whitespace(self):
        """Test parsing JSON with leading/trailing whitespace."""
        response = '  \n  {"key": "value"}  \n  '
        result = extract_json_from_llm_response(response)
        assert result == {"key": "value"}

    def test_json_in_markdown_code_block(self):
        """Test extracting JSON from markdown code block."""
        response = '```json\n{"key": "value", "nested": {"a": 1}}\n```'
        result = extract_json_from_llm_response(response)
        assert result == {"key": "value", "nested": {"a": 1}}

    def test_json_in_markdown_code_block_no_language(self):
        """Test extracting JSON from markdown code block without language tag."""
        response = '```\n{"key": "value"}\n```'
        result = extract_json_from_llm_response(response)
        assert result == {"key": "value"}

    def test_json_in_triple_tilde_block(self):
        """Test extracting JSON from ~~~ code block."""
        response = '~~~json\n{"key": "value"}\n~~~'
        result = extract_json_from_llm_response(response)
        assert result == {"key": "value"}

    def test_json_with_surrounding_text(self):
        """Test extracting JSON from text with explanations."""
        response = 'Here is the analysis result:\n{"key": "value", "count": 5}\nEnd of analysis.'
        result = extract_json_from_llm_response(response)
        assert result == {"key": "value", "count": 5}

    def test_json_with_prefix_text(self):
        """Test extracting JSON when LLM adds explanatory prefix."""
        response = 'Based on the code analysis, here is my assessment:\n\n{"issues": [], "confidence": 0.9}'
        result = extract_json_from_llm_response(response)
        assert result == {"issues": [], "confidence": 0.9}

    def test_nested_json_structures(self):
        """Test extracting complex nested JSON."""
        response = """```json
{
  "issues": [
    {
      "type": "weak-assertion",
      "details": {"line": 10, "severity": "warning"}
    }
  ],
  "summary": {"total": 1}
}
```"""
        result = extract_json_from_llm_response(response)
        assert result == {
            "issues": [
                {
                    "type": "weak-assertion",
                    "details": {"line": 10, "severity": "warning"},
                }
            ],
            "summary": {"total": 1},
        }

    def test_multiple_json_objects_selects_largest(self):
        """Test that when multiple JSON objects exist, the largest is selected."""
        response = 'Small: {"a": 1} and large: {"a": 1, "b": 2, "c": 3, "d": 4}'
        result = extract_json_from_llm_response(response)
        # Should select the larger/more complete JSON
        assert len(result) >= 2

    def test_list_extraction_from_markdown(self):
        """Test extracting JSON array from markdown."""
        response = '```json\n[{"id": 1}, {"id": 2}]\n```'
        result = extract_json_from_llm_response(response, expected_type=list)
        assert result == [{"id": 1}, {"id": 2}]

    def test_empty_response_raises_error(self):
        """Test that empty response raises JSONExtractionError."""
        with pytest.raises(JSONExtractionError) as exc_info:
            extract_json_from_llm_response("")
        assert "Empty response" in str(exc_info.value)

    def test_whitespace_only_response_raises_error(self):
        """Test that whitespace-only response raises error."""
        with pytest.raises(JSONExtractionError) as exc_info:
            extract_json_from_llm_response("   \n\n   ")
        assert "Empty response" in str(exc_info.value)

    def test_no_json_found_raises_error(self):
        """Test that text without JSON raises JSONExtractionError."""
        response = "This is just plain text without any JSON structure."
        with pytest.raises(JSONExtractionError) as exc_info:
            extract_json_from_llm_response(response)
        assert "No valid JSON" in str(exc_info.value)

    def test_invalid_json_raises_error(self):
        """Test that invalid JSON syntax raises error."""
        response = '```json\n{key: "value"}\n```'  # Missing quotes on key
        with pytest.raises(JSONExtractionError):
            extract_json_from_llm_response(response)

    def test_type_mismatch_continues_searching(self):
        """Test that type mismatch causes fallback to other strategies."""
        # Response has dict, but we expect list
        response = '{"key": "value"}'
        with pytest.raises(JSONExtractionError):
            extract_json_from_llm_response(response, expected_type=list)

    def test_real_world_deepseek_response(self):
        """Test parsing a realistic DeepSeek LLM response."""
        response = """Based on my analysis, here are the issues found:

```json
{
  "issues": [
    {
      "type": "weak-assertion",
      "line": 15,
      "severity": "warning",
      "message": "Assertion is too broad",
      "suggestion": "Use more specific assertion",
      "example_code": "assert result == expected_value"
    }
  ],
  "overall_quality": "fair",
  "confidence": 0.85
}
```

This analysis considered the test structure and assertion patterns."""
        result = extract_json_from_llm_response(response)
        assert "issues" in result
        assert result["overall_quality"] == "fair"
        assert result["confidence"] == 0.85
        assert len(result["issues"]) == 1

    def test_malformed_markdown_with_valid_json(self):
        """Test extracting JSON when markdown delimiters are malformed."""
        response = '```json\n{"key": "value"}\n'  # Missing closing ```
        # Should still find the JSON object
        result = extract_json_from_llm_response(response)
        assert result == {"key": "value"}

    def test_json_with_escaped_characters(self):
        """Test parsing JSON with escaped characters."""
        response = r'{"message": "Line 1\nLine 2", "path": "C:\\Users\\test"}'
        result = extract_json_from_llm_response(response)
        assert result["message"] == "Line 1\nLine 2"
        assert "path" in result

    def test_extraction_error_includes_preview(self):
        """Test that JSONExtractionError includes response preview."""
        long_response = "Invalid response " * 100
        with pytest.raises(JSONExtractionError) as exc_info:
            extract_json_from_llm_response(long_response)
        error = exc_info.value
        assert error.response_preview is not None
        assert len(error.response_preview) <= 500


class TestValidateJsonSchema:
    """Test cases for validate_json_schema function."""

    def test_valid_schema_all_fields_present(self):
        """Test validation passes when all required fields present."""
        data = {"field1": "value1", "field2": "value2", "field3": 123}
        required = ["field1", "field2"]
        assert validate_json_schema(data, required) is True

    def test_valid_schema_exact_fields(self):
        """Test validation passes with exactly required fields."""
        data = {"field1": "value1", "field2": "value2"}
        required = ["field1", "field2"]
        assert validate_json_schema(data, required) is True

    def test_invalid_schema_missing_field(self):
        """Test validation fails when required field missing."""
        data = {"field1": "value1"}
        required = ["field1", "field2"]
        assert validate_json_schema(data, required) is False

    def test_invalid_schema_empty_dict(self):
        """Test validation fails for empty dict with required fields."""
        data = {}
        required = ["field1"]
        assert validate_json_schema(data, required) is False

    def test_valid_schema_no_required_fields(self):
        """Test validation passes when no fields required."""
        data = {"field1": "value1"}
        required = []
        assert validate_json_schema(data, required) is True

    def test_invalid_schema_not_dict(self):
        """Test validation fails for non-dict input."""
        data = ["item1", "item2"]
        required = ["field1"]
        assert validate_json_schema(data, required) is False

    def test_valid_schema_none_values(self):
        """Test validation passes with None values in fields."""
        data = {"field1": None, "field2": None}
        required = ["field1", "field2"]
        assert validate_json_schema(data, required) is True


class TestSafeJsonParse:
    """Test cases for safe_json_parse function."""

    def test_valid_json_dict(self):
        """Test parsing valid JSON dict."""
        result = safe_json_parse('{"key": "value"}')
        assert result == {"key": "value"}

    def test_valid_json_list(self):
        """Test parsing valid JSON list."""
        result = safe_json_parse("[1, 2, 3]")
        assert result == [1, 2, 3]

    def test_invalid_json_returns_default(self):
        """Test that invalid JSON returns default value."""
        result = safe_json_parse("not json", default={})
        assert result == {}

    def test_invalid_json_custom_default(self):
        """Test that custom default is returned on failure."""
        result = safe_json_parse("not json", default={"error": "parse_failed"})
        assert result == {"error": "parse_failed"}

    def test_empty_string_returns_default(self):
        """Test that empty string returns default."""
        result = safe_json_parse("", default=None)
        assert result is None

    def test_none_input_returns_default(self):
        """Test that None input returns default."""
        result = safe_json_parse(None, default={})
        assert result == {}

    def test_whitespace_json(self):
        """Test parsing JSON with whitespace."""
        result = safe_json_parse('  {"key": "value"}  ')
        assert result == {"key": "value"}

    def test_no_logging_on_error(self):
        """Test that logging can be disabled."""
        # Should not raise exception even with log_errors=False
        result = safe_json_parse("invalid", default={}, log_errors=False)
        assert result == {}
