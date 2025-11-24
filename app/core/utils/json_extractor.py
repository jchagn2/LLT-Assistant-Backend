"""JSON extraction utilities for parsing LLM responses.

This module provides robust JSON extraction from LLM responses that may
contain markdown formatting, surrounding text, or other formatting issues.
"""

import json
import logging
import re
from typing import Any, Dict, List, Union

logger = logging.getLogger(__name__)


class JSONExtractionError(Exception):
    """Raised when JSON cannot be extracted from response."""

    def __init__(self, message: str, response_preview: str = None):
        super().__init__(message)
        self.response_preview = response_preview


def extract_json_from_llm_response(
    response: str, expected_type: type = dict
) -> Union[Dict[str, Any], List[Any]]:
    """
    Extract JSON from LLM response handling various formats.

    This function attempts multiple strategies to extract valid JSON from
    LLM responses that may be formatted in various ways:
    1. Direct JSON parsing (pure JSON response)
    2. Extraction from markdown code blocks (```json...```)
    3. Finding JSON objects/arrays within text
    4. Handling multiple JSON objects (takes the largest)

    Args:
        response: Raw LLM response string
        expected_type: Expected JSON type (dict or list)

    Returns:
        Parsed JSON object (dict or list)

    Raises:
        JSONExtractionError: If no valid JSON found matching expected type

    Examples:
        >>> extract_json_from_llm_response('{"key": "value"}')
        {'key': 'value'}

        >>> extract_json_from_llm_response('```json\\n{"key": "value"}\\n```')
        {'key': 'value'}

        >>> extract_json_from_llm_response('Here is the result: {"key": "value"}')
        {'key': 'value'}
    """
    if not response or not response.strip():
        raise JSONExtractionError(
            "Empty response received from LLM", response_preview=""
        )

    original_response = response
    response = response.strip()

    # Strategy 1: Try direct parsing first (fastest path)
    try:
        result = json.loads(response)
        if isinstance(result, expected_type):
            logger.debug("Successfully parsed JSON directly")
            return result
        else:
            logger.debug(
                "Parsed JSON but type mismatch: expected %s, got %s",
                expected_type.__name__,
                type(result).__name__,
            )
    except json.JSONDecodeError:
        logger.debug("Direct JSON parsing failed, trying extraction strategies")

    # Strategy 2: Extract from markdown code blocks
    json_from_markdown = _extract_from_markdown(response, expected_type)
    if json_from_markdown is not None:
        logger.debug("Successfully extracted JSON from markdown code block")
        return json_from_markdown

    # Strategy 3: Find JSON objects/arrays in text
    json_from_text = _extract_from_text(response, expected_type)
    if json_from_text is not None:
        logger.debug("Successfully extracted JSON from surrounding text")
        return json_from_text

    # All strategies failed
    preview = (
        original_response[:500] if len(original_response) > 500 else original_response
    )
    raise JSONExtractionError(
        f"No valid JSON of type {expected_type.__name__} found in response",
        response_preview=preview,
    )


def _extract_from_markdown(
    response: str, expected_type: type
) -> Union[Dict[str, Any], List[Any], None]:
    """
    Extract JSON from markdown code blocks.

    Handles formats like:
    - ```json\\n{...}\\n```
    - ```\\n{...}\\n```
    - ~~~json\\n{...}\\n~~~

    Args:
        response: Response text
        expected_type: Expected JSON type

    Returns:
        Parsed JSON or None if extraction fails
    """
    # Try different code block patterns
    patterns = [
        r"```(?:json)?\s*(\{.*?\})\s*```",  # Object in code block
        r"```(?:json)?\s*(\[.*?\])\s*```",  # Array in code block
        r"~~~(?:json)?\s*(\{.*?\})\s*~~~",  # Object with ~~~ delimiter
        r"~~~(?:json)?\s*(\[.*?\])\s*~~~",  # Array with ~~~ delimiter
    ]

    for pattern in patterns:
        matches = re.findall(pattern, response, re.DOTALL | re.IGNORECASE)
        for match in matches:
            try:
                result = json.loads(match)
                if isinstance(result, expected_type):
                    return result
            except json.JSONDecodeError:
                continue

    return None


def _extract_from_text(
    response: str, expected_type: type
) -> Union[Dict[str, Any], List[Any], None]:
    """
    Extract JSON from text by finding JSON objects/arrays.

    Uses regex to find potential JSON structures and validates them.

    Args:
        response: Response text
        expected_type: Expected JSON type

    Returns:
        Parsed JSON or None if extraction fails
    """
    if expected_type == dict:
        # Find JSON objects (nested braces supported)
        json_pattern = r"\{(?:[^{}]|\{(?:[^{}]|\{[^{}]*\})*\})*\}"
    elif expected_type == list:
        # Find JSON arrays (nested brackets supported)
        json_pattern = r"\[(?:[^\[\]]|\[(?:[^\[\]]|\[[^\[\]]*\])*\])*\]"
    else:
        return None

    matches = re.findall(json_pattern, response, re.DOTALL)

    # Try each match, preferring larger/more complete JSON structures
    # Sort by length descending to try most complete matches first
    matches_sorted = sorted(matches, key=len, reverse=True)

    for match in matches_sorted:
        try:
            result = json.loads(match)
            if isinstance(result, expected_type):
                # Basic sanity check: JSON should have some content
                if expected_type == dict and len(result) > 0:
                    return result
                elif expected_type == list and len(result) > 0:
                    return result
        except json.JSONDecodeError:
            continue

    return None


def validate_json_schema(data: Dict[str, Any], required_fields: List[str]) -> bool:
    """
    Validate that JSON data contains required fields.

    Args:
        data: JSON data to validate
        required_fields: List of required field names

    Returns:
        True if all required fields present, False otherwise

    Examples:
        >>> validate_json_schema({"a": 1, "b": 2}, ["a", "b"])
        True

        >>> validate_json_schema({"a": 1}, ["a", "b"])
        False
    """
    if not isinstance(data, dict):
        return False

    return all(field in data for field in required_fields)


def safe_json_parse(response: str, default: Any = None, log_errors: bool = True) -> Any:
    """
    Safely parse JSON with fallback to default value.

    Args:
        response: JSON string to parse
        default: Default value if parsing fails
        log_errors: Whether to log parsing errors

    Returns:
        Parsed JSON or default value

    Examples:
        >>> safe_json_parse('{"key": "value"}', default={})
        {'key': 'value'}

        >>> safe_json_parse('invalid json', default={})
        {}
    """
    try:
        return json.loads(response.strip())
    except (json.JSONDecodeError, AttributeError) as e:
        if log_errors:
            logger.warning("Failed to parse JSON: %s", e)
        return default
