from unittest.mock import MagicMock

import pytest

from app.analyzers.ast_parser import ParsedTestFile, TestClassInfo, TestFunctionInfo
from app.core.analysis.uncertain_case_detector import UncertainCaseDetector


@pytest.fixture
def detector():
    return UncertainCaseDetector()


def create_mock_func(
    name, assertions=[], decorators=[], source_code="", line_number=1, class_name=None
):
    """Create a mock TestFunctionInfo object for testing.

    Note: We need to set line_number and class_name to make the function hashable
    via the tuple (name, line_number, class_name) used in the actual implementation.
    """
    func = MagicMock(spec=TestFunctionInfo)
    func.name = name
    func.assertions = assertions
    func.decorators = decorators
    func.source_code = source_code
    func.line_number = line_number
    func.class_name = class_name
    return func


def test_identify_uncertain_cases_similar_names(detector):
    # Use lower similarity threshold to match actual calculated similarity (0.5)
    # "test_user_creation_success" vs "test_user_creation_failure"
    # After removing "test": {"user", "creation", "success"} vs {"user", "creation", "failure"}
    # Shared: 2 (user, creation), Union: 4, Similarity: 0.5
    detector_low_threshold = UncertainCaseDetector(similarity_threshold=0.5)

    # Create functions with different line numbers to ensure uniqueness
    func1 = create_mock_func(
        "test_user_creation_success", line_number=10, class_name="TestUser"
    )
    func2 = create_mock_func(
        "test_user_creation_failure", line_number=20, class_name="TestUser"
    )
    func3 = create_mock_func("test_product_update_logic", line_number=30)
    parsed_file = MagicMock(spec=ParsedTestFile)
    parsed_file.test_functions = [func1, func2, func3]
    parsed_file.test_classes = []

    uncertain = detector_low_threshold.identify_uncertain_cases(parsed_file)
    # Similar functions should be detected (both in same class with similar names)
    assert func1 in uncertain
    assert func2 in uncertain
    assert func3 not in uncertain


def test_identify_uncertain_cases_complex_assertions(detector):
    assertion1 = MagicMock()
    assertion1.assertion_type = "equality"
    assertion2 = MagicMock()
    assertion2.assertion_type = "other"
    assertion3 = MagicMock()
    assertion3.assertion_type = "other"

    # Need more assertions to trigger complexity detection (default min is 5)
    func1 = create_mock_func("check_complex_output_validation", line_number=10)
    func1.assertions = [
        assertion1,
        assertion1,
        assertion1,
        assertion1,
        assertion1,
        assertion2,
    ]
    func2 = create_mock_func("verify_simple_return_value", line_number=20)
    func2.assertions = [assertion1]

    parsed_file = MagicMock(spec=ParsedTestFile)
    parsed_file.test_functions = [func1, func2]
    parsed_file.test_classes = []

    uncertain = detector.identify_uncertain_cases(parsed_file)
    assert func1 in uncertain
    assert func2 not in uncertain


def test_identify_uncertain_cases_unusual_patterns(detector):
    func1 = create_mock_func("test_case_with_sleep_call", line_number=10)
    func1.source_code = "import time; time.sleep(1)"
    func2 = create_mock_func("test_case_with_global_keyword", line_number=20)
    func2.source_code = "global x; x = 1"
    func3 = create_mock_func("test_case_with_many_decorators", line_number=30)
    func3.decorators = [
        1,
        2,
        3,
        4,
        5,
    ]  # Need 5 decorators (min_decorators default is 4)
    func4 = create_mock_func("a_regular_test_case_for_patterns", line_number=40)

    parsed_file = MagicMock(spec=ParsedTestFile)
    parsed_file.test_functions = [func1, func2, func3, func4]
    parsed_file.test_classes = []

    uncertain = detector.identify_uncertain_cases(parsed_file)
    assert func1 in uncertain  # has test smell (sleep)
    assert func2 in uncertain  # has test smell (global)
    assert func3 in uncertain  # has unusual decorator pattern
    assert func4 not in uncertain


def test_calculate_name_similarity(detector):
    # Test the _calculate_name_similarity method instead of removed _are_similar_functions
    name1 = "test_get_user_by_id"
    name2 = "test_get_user_by_name"
    name3 = "test_delete_product_completely"

    similarity_12 = detector._calculate_name_similarity(name1, name2)
    similarity_13 = detector._calculate_name_similarity(name1, name3)

    # Similar names should have high similarity score
    assert similarity_12 > 0.5
    # Dissimilar names should have low similarity score
    assert similarity_13 < 0.5


def test_has_test_smells(detector):
    # Test _has_test_smells method (replaces _has_unusual_patterns)
    func_sleep = create_mock_func(
        "test_sleep", source_code="time.sleep(1)", line_number=10
    )
    func_global = create_mock_func(
        "test_global", source_code="global my_var", line_number=20
    )
    func_normal = create_mock_func("test_normal", source_code="x = 1", line_number=30)

    assert detector._has_test_smells(func_sleep) is True
    assert detector._has_test_smells(func_global) is True
    assert detector._has_test_smells(func_normal) is False


def test_has_unusual_decorator_patterns(detector):
    # Test decorator pattern detection separately
    # More than min_decorators (default is 4)
    func_many_decorators = create_mock_func(
        "test_decorators", decorators=[1, 2, 3, 4, 5], line_number=10
    )
    func_normal = create_mock_func("test_normal", decorators=[1], line_number=20)

    assert detector._has_unusual_decorator_patterns(func_many_decorators) is True
    assert detector._has_unusual_decorator_patterns(func_normal) is False


def test_no_uncertain_cases(detector):
    func1 = create_mock_func("validate_user_creation_endpoint", line_number=10)
    func2 = create_mock_func("check_product_deletion_behavior", line_number=20)
    parsed_file = MagicMock(spec=ParsedTestFile)
    parsed_file.test_functions = [func1, func2]
    parsed_file.test_classes = []

    uncertain = detector.identify_uncertain_cases(parsed_file)
    assert len(uncertain) == 0


def test_identify_uncertain_cases_in_classes(detector):
    # Use lower similarity threshold to match actual calculated similarity (0.6)
    # "test_similar_in_class_a" vs "test_similar_in_class_b"
    # After removing "test": {"similar", "in", "class", "a"} vs {"similar", "in", "class", "b"}
    # Shared: 3 (similar, in, class), Union: 5, Similarity: 0.6
    detector_low_threshold = UncertainCaseDetector(similarity_threshold=0.6)

    # Functions in same class with similar names should be detected
    class_func1 = create_mock_func(
        "test_similar_in_class_a", line_number=10, class_name="TestSimilar"
    )
    class_func2 = create_mock_func(
        "test_similar_in_class_b", line_number=20, class_name="TestSimilar"
    )
    test_class = MagicMock(spec=TestClassInfo)
    test_class.methods = [class_func1, class_func2]

    parsed_file = MagicMock(spec=ParsedTestFile)
    parsed_file.test_functions = []
    parsed_file.test_classes = [test_class]

    uncertain = detector_low_threshold.identify_uncertain_cases(parsed_file)
    assert class_func1 in uncertain
    assert class_func2 in uncertain
