"""LLM-based analyzer for test code quality issues."""

import json
import logging
from typing import List, Optional, Tuple

from app.analyzers.ast_parser import ParsedTestFile, TestFunctionInfo
from app.api.v1.schemas import Issue, IssueSuggestion
from app.core.llm.llm_client import LLMClient, create_llm_client
from app.core.utils.json_extractor import (
    JSONExtractionError,
    extract_json_from_llm_response,
    validate_json_schema,
)

logger = logging.getLogger(__name__)

# System prompts for different analysis types

MERGEABILITY_SYSTEM_PROMPT = """
You are an expert Python pytest analyzer specializing in test code quality.
Your task is to analyze test functions and determine if they can be merged
while maintaining clarity and following the single responsibility principle.

CRITICAL OUTPUT REQUIREMENTS:
1. Respond ONLY with valid JSON
2. Do NOT include any explanatory text before or after the JSON
3. Do NOT wrap the JSON in markdown code blocks (no ```)
4. Do NOT use comments in the JSON
5. Ensure all string values are properly quoted

Your response must match this EXACT format:
{
  "mergeable": true,
  "confidence": 0.85,
  "reason": "explanation of why tests can/cannot be merged",
  "merged_test_name": "suggested name if mergeable",
  "concerns": ["any potential issues with merging"]
}

Note: Use boolean true/false (not strings), and confidence must be a number between 0.0 and 1.0.
"""

ASSERTION_QUALITY_SYSTEM_PROMPT = """
You are a pytest testing expert. Analyze test assertions to determine if they
adequately verify the expected behavior. Identify weak, missing, or redundant
assertions.

CRITICAL OUTPUT REQUIREMENTS:
1. Respond ONLY with valid JSON
2. Do NOT include any explanatory text before or after the JSON
3. Do NOT wrap the JSON in markdown code blocks (no ```)
4. Do NOT use comments in the JSON
5. Ensure all string values are properly quoted

Your response must match this EXACT format:
{
  "issues": [
    {
      "type": "weak-assertion",
      "line": 10,
      "severity": "warning",
      "message": "description of the issue",
      "suggestion": "how to improve the assertion",
      "example_code": "suggested code fix"
    }
  ],
  "overall_quality": "fair",
  "confidence": 0.85
}

Valid values:
- type: "weak-assertion", "missing-assertion", or "over-assertion"
- severity: "error", "warning", or "info"
- overall_quality: "poor", "fair", "good", or "excellent"
- confidence: number between 0.0 and 1.0
- line: integer line number
"""

TEST_SMELL_SYSTEM_PROMPT = """
You are a senior test engineer. Identify code smells in pytest test code that
could lead to flaky tests, maintenance issues, or false positives/negatives.

CRITICAL OUTPUT REQUIREMENTS:
1. Respond ONLY with valid JSON
2. Do NOT include any explanatory text before or after the JSON
3. Do NOT wrap the JSON in markdown code blocks (no ```)
4. Do NOT use comments in the JSON
5. Ensure all string values are properly quoted

Your response must match this EXACT format:
{
  "smells": [
    {
      "type": "test-smell-category",
      "line": 10,
      "severity": "warning",
      "description": "what the smell is",
      "impact": "why this is problematic",
      "suggestion": "how to fix it",
      "example_code": "improved code"
    }
  ],
  "confidence": 0.85
}

Valid values:
- severity: "error", "warning", or "info"
- confidence: number between 0.0 and 1.0
- line: integer line number

Common test smells to detect:
- time.sleep() usage (flaky timing)
- Global state modification
- Test order dependencies
- Over-mocking (too many @patch decorators)
- Hard-coded credentials or URLs
- Missing cleanup logic
"""

# User prompt templates

MERGEABILITY_USER_PROMPT = """
Analyze if these test functions can be merged:
```python
{test_function_1_code}
```
```python
{test_function_2_code}
```

Context:
- Both tests are in the same test class: {class_name}
- They test the same module: {module_name}
- Current test file has {total_tests} test functions

Consider:
1. Do they test the same behavior/feature?
2. Would merging reduce clarity or violate single responsibility?
3. Are there setup/teardown dependencies?
"""

ASSERTION_QUALITY_USER_PROMPT = """
Analyze the assertion quality in this test function:
```python
{test_function_code}
```

Function being tested:
```python
{implementation_code}  # If available
```

Evaluate:
1. Are assertions testing the right things?
2. Are there missing edge cases?
3. Are assertions too broad (e.g., assert len(x) > 0 instead of assert len(x) == 5)?
4. Are there any redundant assertions?
5. Should exceptions be tested with pytest.raises?

Focus on practical improvements that enhance test reliability.
"""

TEST_SMELL_USER_PROMPT = """
Detect test code smells in this test function:
```python
{test_function_code}
```

Full test class context:
```python
{test_class_code}  # If applicable
```

Pay special attention to:
1. Timing-dependent operations (sleep, polling)
2. External dependencies (network, filesystem, databases)
3. Shared state between tests
4. Complex mock setups that obscure test intent
"""


class LLMAnalyzer:
    """Handles LLM-based analysis of test code."""

    def __init__(self, llm_client: Optional[LLMClient] = None):
        self.client = llm_client or create_llm_client()

    async def analyze_mergeability(
        self, test1: TestFunctionInfo, test2: TestFunctionInfo, context: ParsedTestFile
    ) -> Optional[Issue]:
        """Check if two tests can be merged."""
        max_retries = 2

        for attempt in range(max_retries):
            try:
                system_prompt = MERGEABILITY_SYSTEM_PROMPT

                # Add stronger emphasis on JSON format for retries
                if attempt > 0:
                    system_prompt += "\n\nREMINDER: Your response must be pure JSON only. No markdown, no explanations."

                user_prompt = MERGEABILITY_USER_PROMPT.format(
                    test_function_1_code=test1.source_code,
                    test_function_2_code=test2.source_code,
                    class_name=test1.class_name or "module-level",
                    module_name=context.file_path,
                    total_tests=len(context.test_functions)
                    + sum(len(cls.methods) for cls in context.test_classes),
                )

                response = await self.client.chat_completion(
                    [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ]
                )

                # Use robust JSON extraction
                result = extract_json_from_llm_response(response, expected_type=dict)

                # Validate schema
                if not validate_json_schema(result, ["mergeable", "confidence"]):
                    logger.warning(
                        "LLM response missing required fields (attempt %d/%d)",
                        attempt + 1,
                        max_retries,
                    )
                    if attempt < max_retries - 1:
                        continue
                    return None

                if result["mergeable"] and result["confidence"] > 0.7:
                    suggestion = IssueSuggestion(
                        action="replace",
                        old_code=f"{test1.source_code}\n\n{test2.source_code}",
                        new_code=f"# TODO: Merged test function\n# {result.get('reason', 'Tests can be merged')}",
                        explanation=result.get("reason", "Tests can be merged"),
                    )

                    return Issue(
                        file=context.file_path,
                        line=test1.line_number,
                        column=0,
                        severity="info",
                        type="mergeable-tests",
                        message=f"Tests '{test1.name}' and '{test2.name}' could be merged: {result.get('reason', '')}",
                        detected_by="llm",
                        suggestion=suggestion,
                    )

                return None

            except JSONExtractionError as e:
                logger.warning(
                    "Failed to extract JSON from LLM response (attempt %d/%d): %s",
                    attempt + 1,
                    max_retries,
                    e,
                )
                if e.response_preview:
                    logger.debug("Response preview: %s", e.response_preview)

                if attempt < max_retries - 1:
                    continue

                logger.error(
                    "All JSON extraction attempts failed for mergeability analysis"
                )
                return None

            except Exception as e:
                logger.error(f"Error in mergeability analysis: {e}", exc_info=True)
                return None

        return None

    async def analyze_assertion_quality(
        self,
        test_func: TestFunctionInfo,
        context: ParsedTestFile,
        implementation_code: Optional[str] = None,
    ) -> List[Issue]:
        """Analyze assertion quality in a test function."""
        max_retries = 2

        for attempt in range(max_retries):
            try:
                system_prompt = ASSERTION_QUALITY_SYSTEM_PROMPT

                # Add stronger emphasis on JSON format for retries
                if attempt > 0:
                    system_prompt += "\n\nREMINDER: Your response must be pure JSON only. No markdown, no explanations."

                user_prompt = ASSERTION_QUALITY_USER_PROMPT.format(
                    test_function_code=test_func.source_code,
                    implementation_code=implementation_code
                    or "# Implementation not available",
                )

                response = await self.client.chat_completion(
                    [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ]
                )

                # Use robust JSON extraction
                result = extract_json_from_llm_response(response, expected_type=dict)

                # Validate schema
                if not validate_json_schema(result, ["issues"]):
                    logger.warning(
                        "LLM response missing 'issues' field (attempt %d/%d)",
                        attempt + 1,
                        max_retries,
                    )
                    if attempt < max_retries - 1:
                        continue
                    return []

                issues = []
                for issue_data in result.get("issues", []):
                    # Check confidence if present
                    confidence = issue_data.get(
                        "confidence", result.get("confidence", 1.0)
                    )
                    if confidence <= 0.7:
                        continue

                    suggestion = IssueSuggestion(
                        action="replace",
                        old_code=None,
                        new_code=issue_data.get("example_code"),
                        explanation=issue_data.get("suggestion", ""),
                    )

                    issues.append(
                        Issue(
                            file=context.file_path,
                            line=test_func.line_number + issue_data.get("line", 1) - 1,
                            column=0,
                            severity=issue_data.get("severity", "warning"),
                            type=f"llm-{issue_data.get('type', 'assertion-issue')}",
                            message=issue_data.get(
                                "message", "Assertion quality issue detected"
                            ),
                            detected_by="llm",
                            suggestion=suggestion,
                        )
                    )

                return issues

            except JSONExtractionError as e:
                logger.warning(
                    "Failed to extract JSON from LLM response (attempt %d/%d): %s",
                    attempt + 1,
                    max_retries,
                    e,
                )
                if e.response_preview:
                    logger.debug("Response preview: %s", e.response_preview)

                if attempt < max_retries - 1:
                    continue

                logger.error(
                    "All JSON extraction attempts failed for assertion quality analysis"
                )
                return []

            except Exception as e:
                logger.error(f"Error in assertion quality analysis: {e}", exc_info=True)
                return []

        return []

    async def analyze_test_smells(
        self,
        test_func: TestFunctionInfo,
        context: ParsedTestFile,
        test_class_code: Optional[str] = None,
    ) -> List[Issue]:
        """Analyze test code smells."""
        max_retries = 2

        for attempt in range(max_retries):
            try:
                system_prompt = TEST_SMELL_SYSTEM_PROMPT

                # Add stronger emphasis on JSON format for retries
                if attempt > 0:
                    system_prompt += "\n\nREMINDER: Your response must be pure JSON only. No markdown, no explanations."

                user_prompt = TEST_SMELL_USER_PROMPT.format(
                    test_function_code=test_func.source_code,
                    test_class_code=test_class_code or "# No test class context",
                )

                response = await self.client.chat_completion(
                    [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ]
                )

                # Use robust JSON extraction
                result = extract_json_from_llm_response(response, expected_type=dict)

                # Validate schema
                if not validate_json_schema(result, ["smells"]):
                    logger.warning(
                        "LLM response missing 'smells' field (attempt %d/%d)",
                        attempt + 1,
                        max_retries,
                    )
                    if attempt < max_retries - 1:
                        continue
                    return []

                issues = []
                for smell_data in result.get("smells", []):
                    # Check confidence if present
                    confidence = smell_data.get(
                        "confidence", result.get("confidence", 1.0)
                    )
                    if confidence <= 0.7:
                        continue

                    suggestion = IssueSuggestion(
                        action="replace",
                        old_code=None,
                        new_code=smell_data.get("example_code"),
                        explanation=f"{smell_data.get('description', '')}. {smell_data.get('suggestion', '')}",
                    )

                    issues.append(
                        Issue(
                            file=context.file_path,
                            line=test_func.line_number + smell_data.get("line", 1) - 1,
                            column=0,
                            severity=smell_data.get("severity", "warning"),
                            type=f"test-smell-{smell_data.get('type', 'unknown')}",
                            message=f"Test smell: {smell_data.get('description', 'Code smell detected')}",
                            detected_by="llm",
                            suggestion=suggestion,
                        )
                    )

                return issues

            except JSONExtractionError as e:
                logger.warning(
                    "Failed to extract JSON from LLM response (attempt %d/%d): %s",
                    attempt + 1,
                    max_retries,
                    e,
                )
                if e.response_preview:
                    logger.debug("Response preview: %s", e.response_preview)

                if attempt < max_retries - 1:
                    continue

                logger.error(
                    "All JSON extraction attempts failed for test smell analysis"
                )
                return []

            except Exception as e:
                logger.error(f"Error in test smell analysis: {e}", exc_info=True)
                return []

        return []

    async def find_similar_tests(
        self, test_functions: List[TestFunctionInfo], context: ParsedTestFile
    ) -> List[Tuple[TestFunctionInfo, TestFunctionInfo]]:
        """Find pairs of test functions that might be mergeable."""
        similar_pairs = []

        # Simple heuristic: tests with similar names in the same class
        for i, test1 in enumerate(test_functions):
            for j, test2 in enumerate(test_functions[i + 1 :], i + 1):
                # Check if tests are in the same class (or both at module level)
                if test1.class_name == test2.class_name:
                    # Check for similar names
                    name1_parts = test1.name.split("_")
                    name2_parts = test2.name.split("_")

                    # If they share most words, they might be similar
                    common_parts = set(name1_parts) & set(name2_parts)
                    if len(common_parts) >= min(len(name1_parts), len(name2_parts)) - 1:
                        similar_pairs.append((test1, test2))

        return similar_pairs

    async def close(self) -> None:
        """Close the LLM client."""
        await self.client.close()
